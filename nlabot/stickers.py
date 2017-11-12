#   encoding: utf-8
#   stickers.py

from random import randint

# TODO: use getStickers to get sticker pack with ids
SUCCESS = ['CAADBAAD0gIAAlI5kwbFm0b9e6ezGQI',
           'CAADAgAD4QADNuwbBW5uM6aRdOCbAg',
           'CAADBAADuAMAAlI5kwbThupzSIc0CQI',
           'CAADAgADdAcAAlOx9wP2aGQDAAEeKfQC',
           'CAADBQAD-gADR5XbAWtSgBKOL_fFAg']
SORRY = ['CAADAgADBAADijc4AAFx0NNqDnJm4QI', 'CAADAgADBgADijc4AAH50MoMENn2lQI',
         'CAADAgADDgADijc4AAGOGq6J30OGfwI', 'CAADAgADEgADijc4AAF00GirhpifXQI',
         'CAADAgADFAADijc4AAGtl5dISqHmiAI', 'CAADAgADFgADijc4AAErJ-ihzzsO7wI',
         'CAADAgADGwADijc4AAEdwByBSe9kgQI', 'CAADAgADHQADijc4AAEw0RBgpCTPAAEC',
         'CAADAgADHwADijc4AAFXWsuIC4i6fAI']
TRY = ['CAADAgADSwAD4FP5CycQs-qvf8GBAg', 'CAADBAAD2AIAAlI5kwa4IYnU6rFSuAI',
       'CAADBAADzAIAAlI5kwZs9nlnbC5cTgI', 'CAADBAADlwMAAlI5kwayXLLrd21tpAI',
       'CAADBAAD1gIAAlI5kwbUol2GEfKhHQI', 'CAADBAAD2gIAAlI5kwZfjbEodl4riQI',
       'CAADAgADTgAD4FP5C_W-1YHvi0cYAg', 'CAADAgADFAAD4FP5C75navrL1cHAAg',
       'CAADAgADFwAD4FP5C0q5UW3A8qxPAg', 'CAADAgADFgAD4FP5C-_9iCNax_siAg',
       'CAADAgADGAAD4FP5C0gLHKTxveR4Ag', 'CAADAgADKwAD4FP5CzoKTHHnVGQoAg',
       'CAADAgADRwAD4FP5Cw8GVjPle2rxAg'] + SORRY
FAIL = ['CAADAgADYwEAAjbsGwXkTe2zgRvwWAI',
        'CAADAgADJQEAAjbsGwX1CuOrgYRKAAEC']


def get_random_sticker(group):
    i = randint(0, len(group)-1)
    return group[i]
