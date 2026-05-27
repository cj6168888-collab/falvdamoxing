# -*- coding: utf-8 -*-
# Verify the Chinese characters

chars = {
    '对手名称': '\u5bf9\u624b\u540d\u79f0',
    '对手类型': '\u5bf9\u624b\u7c7b\u578b',
    '我方证据': '\u6211\u65b9\u8bc1\u636e',
    '对方证据': '\u5bf9\u65b9\u8bc1\u636e',
}

for name, char in chars.items():
    print(f'{name}: {char} = {char.encode("utf-8").hex()}')
