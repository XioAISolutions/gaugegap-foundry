from gaugegap.lottery_sources import (
    filter_draw_dates,
    merge_draw_sources,
    parse_wclc_recent_html,
    parse_wclc_since_inception_text,
)


def test_parse_wclc_pdf_text_rows():
    text = """
    August 1, 2026 8 22 37 41 43 44 12 12345678
    August 5, 2026 12 30 31 35 41 48 21 12345679
    """
    draws = parse_wclc_since_inception_text(text)
    assert draws[0].draw_date == "2026-08-01"
    assert draws[0].numbers == (8, 22, 37, 41, 43, 44)
    assert draws[0].bonus == 12
    assert draws[1].bonus == 21


def test_parse_wclc_recent_html():
    html = """
    <h4>Saturday, August 15, 2026</h4>
    <div>CLASSIC DRAW</div><li>1</li><li>9</li><li>17</li><li>34</li><li>36</li><li>43</li><li>Bonus 24</li>
    <div>GOLD BALL DRAW</div>
    <h4>Wednesday, August 12, 2026</h4>
    <div>CLASSIC DRAW</div><li>6</li><li>13</li><li>28</li><li>34</li><li>45</li><li>48</li><li>Bonus 46</li>
    """
    draws = parse_wclc_recent_html(html)
    assert [draw.draw_date for draw in draws] == ["2026-08-12", "2026-08-15"]
    assert draws[-1].numbers == (1, 9, 17, 34, 36, 43)
    assert draws[-1].bonus == 24


def test_recent_source_overrides_snapshot_on_same_date():
    old = parse_wclc_since_inception_text("August 15, 2026 1 2 3 4 5 6 7")
    recent = parse_wclc_recent_html(
        "<h4>Saturday, August 15, 2026</h4><div>CLASSIC DRAW</div>"
        "<i>1</i><i>9</i><i>17</i><i>34</i><i>36</i><i>43</i><i>Bonus 24</i><div>GOLD BALL DRAW</div>"
    )
    merged = merge_draw_sources(old, recent)
    assert merged[0].numbers == (1, 9, 17, 34, 36, 43)


def test_filter_dates_is_inclusive():
    draws = parse_wclc_since_inception_text(
        "August 1, 2026 8 22 37 41 43 44 12\n"
        "August 5, 2026 12 30 31 35 41 48 21\n"
        "August 8, 2026 3 7 18 24 45 48 29\n"
    )
    selected = filter_draw_dates(draws, start_date="2026-08-05", end_date="2026-08-08")
    assert [draw.draw_date for draw in selected] == ["2026-08-05", "2026-08-08"]
