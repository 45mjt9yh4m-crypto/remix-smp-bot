from bot.cogs.wordfilter import find_banned, load_words, normalize, save_words

WORDS = ["scemo", "stupid*", "noob", "lol"]


def test_normalize_tricks():
    assert normalize("SCÈMO") == "scemo"
    assert normalize("sc3m0") == "scemo"
    assert normalize("s.c.e.m.o") == "scemo"
    assert normalize("scemoooo") == "scemo"


def test_finds_whole_words_and_variants():
    assert find_banned("sei uno scemo", WORDS) == "scemo"
    assert find_banned("SC3M0!!", WORDS) == "scemo"
    assert find_banned("che stupida", WORDS) == "stupid*"
    assert find_banned("n o o b", WORDS) == "noob"
    assert find_banned("l o l", WORDS) is None  # parole sotto le 4 lettere: niente controllo senza spazi
    assert find_banned("s c e m o", WORDS) == "scemo"


def test_no_false_positives():
    assert find_banned("ciao a tutti, bella partita", WORDS) is None
    assert find_banned("noobmaster è il mio nick", WORDS) is None
    assert find_banned("", WORDS) is None


def test_words_file_roundtrip(tmp_path):
    path = tmp_path / "data" / "parole.json"
    default = tmp_path / "iniziali.json"
    assert load_words(path, default) == []
    default.write_text('["x"]')
    assert load_words(path, default) == ["x"]
    save_words(["b", "a", "a"], path)
    assert load_words(path, default) == ["a", "b"]
