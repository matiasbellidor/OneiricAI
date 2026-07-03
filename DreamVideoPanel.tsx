"""Anti-Fake Engine tests — the demo's two example dreams live here too,
so what the jury sees on screen is exactly what the tests guarantee.

Run from backend/:  python -m pytest app/tests -q
"""

from datetime import timedelta

from ..services import antifake, lexicon
from ..services.wearables.synthetic import SyntheticSource

REAL_CALM_DREAM = (
    "Estaba en la casa de mi abuela en Lan\u00fas. Olor a pan reci\u00e9n hecho, la luz "
    "dorada de la tarde entrando por la ventana del patio. Todo era lento y "
    "c\u00e1lido, como cuando era chico. Mi perro Sim\u00f3n me esperaba en la puerta, "
    "moviendo la cola despacio. Me qued\u00e9 ah\u00ed, en silencio, sin ganas de despertarme."
)

FAKE_VIRAL_DREAM = (
    "Me persegu\u00eda un tsunami gigante por la 9 de Julio. Corr\u00eda entre autos en "
    "llamas mientras explotaba todo a mi alrededor. Salt\u00e9 desde un edificio a un "
    "helic\u00f3ptero en movimiento, la gente gritaba, hab\u00eda fuego por todos lados. "
    "Sent\u00ed p\u00e1nico total pero igual segu\u00ed corriendo a toda velocidad."
)

NIGHT = SyntheticSource(seed=42).fetch_night("test-user", "2026-07-02")
REPORTED = NIGHT.end_ts + timedelta(hours=2)  # written mid-morning


def test_real_calm_dream_passes():
    structured = lexicon.analyze(REAL_CALM_DREAM)
    report = antifake.evaluate(structured, NIGHT, reported_at=REPORTED)
    assert report.passed, f"expected pass, got {report.score}"
    assert report.score >= 80
    assert all(c.passed for c in report.checks)


def test_invented_viral_dream_is_rejected():
    structured = lexicon.analyze(FAKE_VIRAL_DREAM)
    report = antifake.evaluate(structured, NIGHT, reported_at=REPORTED)
    assert not report.passed, f"expected rejection, got {report.score}"
    failing = {c.key for c in report.checks if not c.passed}
    assert "arousal_match" in failing  # heart didn't live that story
    assert "valence_match" in failing  # no stress markers that night


def test_no_sleep_data_is_rejected():
    structured = lexicon.analyze(REAL_CALM_DREAM)
    report = antifake.evaluate(structured, None)
    assert not report.passed
    assert report.score == 0
    assert report.checks[0].key == "session_exists"


def test_stale_report_loses_freshness_points():
    structured = lexicon.analyze(REAL_CALM_DREAM)
    late = NIGHT.end_ts + timedelta(hours=30)
    report = antifake.evaluate(structured, NIGHT, reported_at=late)
    fresh = next(c for c in report.checks if c.key == "freshness")
    assert fresh.points <= 3


if __name__ == "__main__":
    for structured, name in [(lexicon.analyze(REAL_CALM_DREAM), "REAL"),
                             (lexicon.analyze(FAKE_VIRAL_DREAM), "FAKE")]:
        r = antifake.evaluate(structured, NIGHT, reported_at=REPORTED)
        print(f"{name}: score={r.score} passed={r.passed} "
              f"text_arousal={r.text_arousal} bio_arousal={r.bio_arousal}")
        for c in r.checks:
            print(f"  [{'ok' if c.passed else 'XX'}] {c.label}: {c.points}/{c.max_points} \u2014 {c.reason}")
