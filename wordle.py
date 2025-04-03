import random
import time
import os
import msvcrt
from collections import Counter
from colorama import Fore, Style, init

init()

class WordleGame:
    def __init__(self, words_file="words.txt", word_length=5, max_attempts=6):
        self.word_length = word_length
        self.max_attempts = max_attempts
        self.guess_history = []
        self.restricted_keys = []
        self.used_colors = {}
        self.valid_words = self.load_words(words_file)
        self.target_word = random.choice(list(self.valid_words))

    def load_words(self, words_file):
        with open(words_file, "r") as file:
            words = [line.strip().upper() for line in file if len(line.strip()) == self.word_length]
        return words

    def soft_clear(self):
        print("\033[H\033[J", end='', flush=True)
    
    def hide_cursor(self):
        print("\033[?25l", end='', flush=True)

    def show_cursor(self):
        print("\033[?25h", end='', flush=True)

    def type_message(self, message: str, newline: bool = True, delay: float = 0.05):
        for character in message:
            print(character, end='', flush=True)
            time.sleep(delay)
        if newline:
            print()

    def blinking_message(self, message: str, blink_times: int = 1, interval: float = 0.5):
        self.type_message(message, False)
        time.sleep(interval)
        print('\r', end='', flush=True)
        for _ in range(blink_times):
            print(' ' * len(message), end='\r', flush=True)
            time.sleep(interval)
            print(message, end='\r', flush=True)
            time.sleep(interval)
        print(message)

    def blink_until_keypress(self, message: str, interval: float = 0.5):
        self.type_message(message, False)
        time.sleep(interval)
        print('\r', end='', flush=True)
        try:
            while True:
                print(' ' * len(message), end='\r', flush=True)
                time.sleep(interval)
                print(message, end='\r', flush=True)
                time.sleep(interval)
                if msvcrt.kbhit():
                    msvcrt.getch()
                    break
        except KeyboardInterrupt:
            pass
        print(message)
    
    def render_keyboard(self):
        rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]

        max_row_length = max(len(row) for row in rows) * 2

        inner_width = max_row_length + 2

        border_top    = "┌" + "─" * inner_width + "┐"
        border_bottom = "└" + "─" * inner_width + "┘"

        print()
        print(border_top)
        for row in rows:
            line = "│ "

            for char in row:
                color = self.used_colors.get(char, Fore.WHITE)
                line += f"{color}{char} {Style.RESET_ALL}"

            used_columns = len(row) * 2

            padding = (inner_width - 1) - used_columns  

            line += " " * padding + "│"
            print(line)

        print(border_bottom)

    def full_render(self, current_render_func=None, error_message=""):
        self.soft_clear()
        for line in self.guess_history:
            print(line)
        if current_render_func:
            current_render_func(error_message=error_message)
        print()
        self.render_keyboard()
    
    def show_blocked_tile(self, render_func, blocked_index, blocked_letter):
        self.soft_clear()  
        for line in self.guess_history:
            print(line)
        render_func(blocked_index=blocked_index, blocked_letter=blocked_letter)
        print()
        self.render_keyboard()
        print(Fore.LIGHTBLACK_EX + "-" * 26 + Style.RESET_ALL)
        message = f"⚠️  {blocked_letter.upper()} is not allowed."
        print(Fore.RED + message + Style.RESET_ALL)
        time.sleep(0.75)
        self.full_render(render_func)
    
    def validate_guess(self, user_guess: str):
        target_count = Counter(self.target_word)
        result = [''] * len(user_guess)
        used_letters = []

        for i in range(len(user_guess)):
            if user_guess[i] == self.target_word[i]:
                result[i] = Fore.GREEN + user_guess[i] + Style.RESET_ALL
                target_count[user_guess[i]] -= 1
                used_letters.append(user_guess[i])
                self.used_colors[user_guess[i]] = Fore.GREEN
        
        for i in range(len(user_guess)):
            if result[i]:
                continue
            if target_count[user_guess[i]] > 0:
                result[i] = Fore.YELLOW + user_guess[i] + Style.RESET_ALL
                target_count[user_guess[i]] -= 1
                used_letters.append(user_guess[i])
                self.used_colors[user_guess[i]] = Fore.YELLOW
            else:
                result[i] = Fore.LIGHTBLACK_EX + user_guess[i] + Style.RESET_ALL
                if user_guess[i] not in used_letters and user_guess[i] not in self.restricted_keys:
                    self.restricted_keys.append(user_guess[i])
                if user_guess[i] not in self.used_colors:
                    self.used_colors[user_guess[i]] = Fore.BLACK
            
        os.system('cls' if os.name == 'nt' else 'clear')
        return ''.join(result)

    def get_user_guess(self):
        guess = ['_'] * self.word_length
        index = 0

        def render(error_message="", blocked_index=None, blocked_letter=None):
            print(f"\rEnter your guess: ", end='', flush=True)
            if error_message:
                print(Fore.RED + error_message + Style.RESET_ALL, end='', flush=True)
            else:
                for i in range(self.word_length):
                    if blocked_index == i and blocked_letter:
                        print(Fore.RED + '[X]' + Style.RESET_ALL, end=' ')
                    elif guess[i] == '_':
                        print(Fore.LIGHTBLACK_EX + '_' + Style.RESET_ALL, end=' ')
                    else:
                        print(Fore.WHITE + guess[i] + Style.RESET_ALL, end=' ')
        
        self.full_render(render)

        while True:
            key = msvcrt.getwch()

            if key == '\r':
                if index == self.word_length:
                    guess_str = ''.join(guess).upper()
                    if guess_str in self.valid_words:
                        break
                    else:
                        self.full_render(render, error_message="NOT A WORD")
                        time.sleep(0.75)
                        guess = ['_'] * self.word_length
                        index = 0
                        self.full_render(render)
            elif key == '\b':
                if index > 0:
                    index -= 1
                    guess[index] = '_'
                    self.full_render(render)
            elif key.isalpha():
                key_up = key.upper()
                if key_up in self.restricted_keys:
                    self.show_blocked_tile(render, index, key_up)
                elif index < self.word_length:
                    guess[index] = key_up
                    index += 1
                    self.full_render(render)
        print()
        return ''.join(guess)
    
    def run(self):
        self.hide_cursor()
        self.type_message(f"Welcome to {Fore.RED}W{Fore.GREEN}o{Fore.YELLOW}r{Fore.BLUE}d{Fore.MAGENTA}l{Fore.CYAN}e{Style.RESET_ALL}!")
        time.sleep(0.5)
        self.type_message("Your job is to guess 5 letter words. I will provide feedback after each guess.")
        time.sleep(0.5)
        self.type_message("Each letter in your guess will be colored either:")
        time.sleep(0.25)
        self.type_message(f"{Fore.LIGHTBLACK_EX}grey{Style.RESET_ALL} (if the letter is not in the word)...")
        time.sleep(0.25)
        self.type_message(f"{Fore.YELLOW}yellow{Style.RESET_ALL} (if the letter is in the word, but not in the right location), or...")
        time.sleep(0.25)
        self.type_message(f"{Fore.GREEN}green{Style.RESET_ALL} (if the letter is in the word AND is in the right location)...")
        time.sleep(0.25)
        self.blink_until_keypress("Press any button to play!")
        os.system('cls' if os.name == 'nt' else 'clear')

        attempts = 0
        has_won = False

        while attempts < self.max_attempts and not has_won:
            user_guess = self.get_user_guess()
            result = self.validate_guess(user_guess)
            self.guess_history.append(result)
            attempts += 1
            self.full_render()
            if user_guess == self.target_word:
                has_won = True
                break
        
        print()
        if has_won:
            print(Fore.GREEN + f"You guessed it in {attempts} attempts!" + Style.RESET_ALL)
        else:
            print(Fore.RED + f"Out of guesses! The word was: {self.target_word}" + Style.RESET_ALL)
        time.sleep(15)

if __name__ == '__main__':
    game = WordleGame()
    game.run()
