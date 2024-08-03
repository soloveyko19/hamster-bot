import time
from cipher import CipherManager
from daily_reward import ClaimDailyRewardError, DailyRewardManager
from minigame import ClaimError, MinigameManager
from database import Database
import curses
from curses.textpad import Textbox
from threading import Event, Thread


account = None
db = Database("./db.sqlite")


def alert(stdscr: curses.window, text: str):
    stdscr.clear()
    stdscr.addstr(0, 0, text)
    stdscr.addstr(3, 0, "OK (нажмите на любую клавишу)", curses.color_pair(2))
    stdscr.refresh()
    stdscr.getch()


def cipher_option(stdscr: curses.window):
    if not account:
        alert(stdscr, "Сначала нужно войти в аккаунт!")
        return
    cipher_manager = CipherManager(
        auth_key=account.auth_key
    )
    cipher_manager.load_cipher()
    if not cipher_manager.claimed:
        cipher_manager.claim_cipher()
        alert(stdscr, "Награда за шифр успешно получена!")
    else:
        alert(stdscr, "Награда за шифр уже получена")


def loading(stdscr: curses.window, is_loading: Event):
    symbols = ["\\", "|", "/", "-"]
    last_showed = -1
    while not is_loading.is_set():
        last_showed = (last_showed + 1) % 4
        stdscr.clear()
        stdscr.addstr(0, 0, f"Собираем ключ {symbols[last_showed]}")
        stdscr.refresh()
        time.sleep(0.2)


def minigame_option(stdscr: curses.window):
    if not account:
        alert(stdscr, "Сначала нужно войти в аккаунт!")
        return
    
    is_loading = Event()
    loading_thread = Thread(target=loading, args=(stdscr, is_loading))
    loading_thread.start()

    minigame_manager = MinigameManager(
        auth_key=account.auth_key,
        tg_id=account.tg_id
    )
    try:
        minigame_manager.auto_mode()
    except ClaimError:
        is_loading.set()
        loading_thread.join()
        alert(stdscr, "Ключ уже собран или недоступен на данный момент.")
        return
    is_loading.set()
    loading_thread.join()
    alert(stdscr, "Ключ успешно собран!")



def checkout_account(stdscr: curses.window):
    global account
    accounts = db.get_accounts()
    choosen = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Сменить аккаунт", curses.A_BOLD)
        for num, _account in enumerate(accounts):
            stdscr.addstr(num + 2, 0, f"{_account.name} ({_account.tg_id})", curses.A_REVERSE if choosen == num else curses.A_NORMAL)
        stdscr.addstr(len(accounts) + 2, 0, "Вернуться в настройки аккаунта", curses.A_REVERSE if choosen == len(accounts) else curses.A_NORMAL)
        stdscr.refresh()
        key = stdscr.getch()
        match key:
            case 259:
                choosen -= 1
            case 258:
                choosen += 1
            case 10:
                if choosen == len(accounts):
                    return
                elif choosen >= 0 and choosen < len(accounts):
                    account = accounts[choosen]
                    return
        choosen = choosen % (len(accounts) + 1)



def add_account(stdscr: curses.window):
    curses.curs_set(1)
    data_not_valid = False
    try:
        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "Добавление аккаунта", curses.A_BOLD)
            stdscr.addstr(2, 0, "Название аккаунта: ")
            if data_not_valid: stdscr.addstr(12, 0, "Некорректный ввод, данные не могут повторяться с уже существующими!", curses.color_pair(1))
            stdscr.addstr(15, 0, "Enter чтобы сохранить")
            stdscr.addstr(16, 0, "Ctrl + C чтобы выйти")
            name_win = curses.newwin(1, 50, 2, 20)
            name_box = Textbox(name_win)
            stdscr.refresh()
            name_box.edit()
            name = name_box.gather()

            while True:
                stdscr.addstr(3, 0, "Telegram ID: ")
                tg_id_win = curses.newwin(1, 15, 3, 13)
                tg_id_box = Textbox(tg_id_win)
                stdscr.refresh()
                tg_id_box.edit()
                try:
                    tg_id = int(tg_id_box.gather())
                    break
                except (TypeError, ValueError):
                    stdscr.addstr(13, 0, "В Telegram ID могут быть только цифры!", curses.color_pair(1))
            
            stdscr.addstr(4, 0, "Авторизационный ключ: ")
            auth_key_win = curses.newwin(1, 150, 4, 22)
            auth_key_box = Textbox(auth_key_win)
            stdscr.refresh()
            auth_key_box.edit()
            auth_key = auth_key_box.gather()
            try:
                db.add_account(
                    name=name,
                    auth_key=auth_key,
                    tg_id=tg_id
                )
            except Exception:
                data_not_valid = True
                continue
            curses.curs_set(0)
            alert(stdscr, "Аккаунт успешно добавлен!")
            break
    except KeyboardInterrupt:
        return


def delete_account(stdscr: curses.window):
    global account
    accounts = db.get_accounts()
    choosen = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Удаление аккаунта", curses.A_BOLD)
        for num, _account in enumerate(accounts):
            stdscr.addstr(num + 2, 0, f"{_account.name} ({_account.tg_id})", curses.A_REVERSE if choosen == num else curses.A_NORMAL)
        stdscr.addstr(len(accounts) + 2, 0, "Вернуться в настроки аккаунта", curses.A_REVERSE if choosen == len(accounts) else curses.A_NORMAL)
        key = stdscr.getch()
        match key:
            case 259:
                choosen -= 1
            case 258:
                choosen += 1
            case 10:
                if len(accounts) == choosen:
                    break
                else:
                    db.remove_account(accounts[choosen].id)
                    if getattr(account, "id", None) == accounts[choosen].id:
                        account = None
                    alert(stdscr, "Аккаунт был удален!")
                    return                
        choosen = choosen % (len(accounts) + 1)
    


def account_option(stdscr: curses.window):
    choosen = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Настройки аккаунта", curses.A_BOLD)
        stdscr.addstr(2, 0, "Сменить аккаунт", curses.A_REVERSE if choosen == 0 else curses.A_NORMAL)
        stdscr.addstr(3, 0, "Добавить аккаунт", curses.A_REVERSE if choosen == 1 else curses.A_NORMAL)
        stdscr.addstr(4, 0, "Удалить аккаунт", curses.A_REVERSE if choosen == 2 else curses.A_NORMAL)
        stdscr.addstr(5, 0, "Вернуться в меню", curses.A_REVERSE if choosen == 3 else curses.A_NORMAL)
        stdscr.refresh()
        
        key = stdscr.getch()

        match key:
            case 259:
                choosen -= 1
            case 258:
                choosen += 1
            case 10:
                match choosen:
                    case 0:
                        checkout_account(stdscr)
                    case 1:
                        add_account(stdscr)
                    case 2:
                        delete_account(stdscr)
                    case 3:
                        return
        choosen = choosen % 4

def daily_reward_option(stdscr: curses.window):
    if not account:
        alert(stdscr, "Сначала нужно войти в аккаунт!")
        return
    daily_reward_manager = DailyRewardManager(
        auth_key=account.auth_key
    )
    try:
        daily_reward_manager.auto_mode()
    except ClaimDailyRewardError:
        alert(stdscr, "Ежедневная награда уже была получена!")
        return
    alert(stdscr, "Ежедневная награда успешно получена!")    


def create_color_pairs():
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)    
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)    


def show_main_menu(stdscr: curses.window):
    curses.curs_set(0)
    create_color_pairs()
    global account
    choosen = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Главное меню", curses.A_BOLD)
        stdscr.addstr(2, 0, "Ежедневный шифр", curses.A_REVERSE if choosen == 0 else curses.A_NORMAL)
        stdscr.addstr(3, 0, "Мини-игра на ключ", curses.A_REVERSE if choosen == 1 else curses.A_NORMAL)
        stdscr.addstr(4, 0, "Ежедневная награда", curses.A_REVERSE if choosen == 2 else curses.A_NORMAL)
        stdscr.addstr(5, 0, "Настройки аккаунта", curses.A_REVERSE if choosen == 3 else curses.A_NORMAL)
        stdscr.addstr(6, 0, "Выход", curses.A_REVERSE if choosen == 4 else curses.A_NORMAL)
        stdscr.addstr(8, 0, f"Аккаунт - {account.name} ({account.tg_id})" if account else "Вы не авторизованы", curses.A_BOLD)

        stdscr.refresh()

        key = stdscr.getch()

        match key:
            case 259:
                choosen -= 1
            case 258:
                choosen += 1
            case 10:
                stdscr.refresh()
                match choosen:
                    case 0:
                        cipher_option(stdscr)
                    case 1:
                        minigame_option(stdscr)
                    case 2:
                        daily_reward_option(stdscr)
                    case 3:
                        account_option(stdscr)
                    case 4:
                        exit(0)
        choosen = choosen % 5


def run():
    try:
        curses.wrapper(show_main_menu)
    except KeyboardInterrupt:
        exit(0)
