from gaugegap.lottery_multigame_sources import parse_daily_history_text, parse_max_history_text


def test_parse_max_history_ignores_non_date_bonus_draws():
    text = "LOTTO MAX January 1, 2026 1 5 9 13 22 41 52 17 1234567 Maxmillions Draw # 1 1 2 3 4 5 6 7 January 5, 2026 2 6 10 18 31 44 51 4 7654321"
    draws = parse_max_history_text(text)
    assert [row.numbers for row in draws] == [(1, 5, 9, 13, 22, 41, 52), (2, 6, 10, 18, 31, 44, 51)]
    assert [row.bonus for row in draws] == [17, 4]


def test_parse_daily_history_captures_grand_number():
    text = "DAILY GRAND October 20, 2016 8 14 18 35 37 5 6591304 October 24, 2016 8 9 28 36 48 1 3762941 Bonus Draw 1 18 21 38 41 46"
    rows = parse_daily_history_text(text)
    assert rows[0].draw.numbers == (8, 14, 18, 35, 37)
    assert rows[0].grand_number == 5
    assert rows[1].grand_number == 1
