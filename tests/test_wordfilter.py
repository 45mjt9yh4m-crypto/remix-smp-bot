from bot.cogs.wordfilter import find_banned, normalize

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
    assert find_banned("l o l", WORDS) == "lol"
    assert find_banned("s c e m o", WORDS) == "scemo"


def test_no_false_positives():
    assert find_banned("ciao a tutti, bella partita", WORDS) is None
    assert find_banned("noobmaster è il mio nick", WORDS) is None
    assert find_banned("", WORDS) is None


def test_word_list_merges_defaults_added_and_removed(tmp_path):
    from bot.cogs.wordfilter import WordList, write_list

    default, added, removed = tmp_path / "default.json", tmp_path / "data" / "added.json", tmp_path / "data" / "removed.json"
    write_list(["base1", "base2"], default)
    words = WordList(default, added, removed)
    assert words.words == ["base1", "base2"]
    assert words.add("extra") and not words.add("extra")
    assert words.remove("base1") and not words.remove("base1")
    reloaded = WordList(default, added, removed)
    assert reloaded.words == ["base2", "extra"]
    write_list(["base1", "base2", "base3"], default)  # aggiornamento della lista di partenza
    assert WordList(default, added, removed).words == ["base2", "base3", "extra"]
    assert reloaded.add("base1") and WordList(default, added, removed).words == ["base1", "base2", "base3", "extra"]


def test_default_list_blocks_user_variants():
    from bot.cogs.wordfilter import DEFAULT_WORDS_FILE, read_list

    words = read_list(DEFAULT_WORDS_FILE)
    for text in ["nigga", "NIGGERS", "n1gers", "n1.g3rs", "nig3rs", "niggass", "n igga", "n i g g e r", "niiiigger", "ni99a", "you nig", "ngers"]:
        assert find_banned(text, words), text
    for text in ["good night", "nice game gg", "I'm from Nigeria", "ciao a tutti", "spicy food", "raccoon", "Pakistan"]:
        assert find_banned(text, words) is None, text


def test_default_list_other_languages():
    from bot.cogs.wordfilter import DEFAULT_WORDS_FILE, read_list

    words = read_list(DEFAULT_WORDS_FILE)
    for text in ["maricón", "eres un sudaca", "seu viado", "sale bougnoule", "Schwuchtel", "czarnuchy", "ibne", "ты пидорас", "НИГГЕР"]:
        assert find_banned(text, words), text
    for text in ["ele pede ajuda", "ich bin müde", "dat is leuk", "dzień dobry", "pedale della bici", "привет как дела", "хачапури вкусный"]:
        assert find_banned(text, words) is None, text
