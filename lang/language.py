import random

from lang.en import LANGUAGE_EN
from lang.ru import LANGUAGE_RU


class Language:
    LANGS = ['ru', 'en']

    def __init__(self, lang: str = 'ru'):
        self.lang = lang

    def set_lang(self, lang: str):
        if lang in self.LANGS:
            self.lang = lang

    def get_text(self, param: str):
        if self.lang == 'ru':
            language = LANGUAGE_RU
        elif self.lang == 'en':
            language = LANGUAGE_EN
        text = language[param]
        if type(text) == list:
            text = random.choice(text)
        return text
