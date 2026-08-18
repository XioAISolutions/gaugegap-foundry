#!/usr/bin/env python3
"""Seal, score, and evaluate Lottery Forge prospective predictions."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from gaugegap.lottery_forge import LotterySpec
from gaugegap.lottery_prospective import (
    evaluate_scores,
    make_prediction,
    protocol_digest,
    score_prediction,
    verify_prediction,
    verify_score,
)
from gaugegap.lottery_sources import fetch_wclc_649

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "data" / "lottery" / "prospective" / "protocol_v1.json"
LOCAL_TZ = ZoneInfo("America/Toronto")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload, *, immutable: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if immutable and path.exists() and path.read_text(encoding="utf-8") != text:
        raise RuntimeError(f"refusing to overwrite a different immutable artifact: {path}")
    path.write_text(text, encoding="utf-8")


def spec_from_protocol(protocol) -> LotterySpec:
    game = protocol["game"]
    return LotterySpec(str(game["name"]), int(game["pool_size"]), int(game["pick_count"]))


def source_summary(meta):
    sources = []
    for source in meta.get("sources", []):
        if isinstance(source, dict):
            sources.append({key: source[key] for key in ("kind", "url", "sha256", "bytes") if key in source})
    return {
        "kind": meta.get("kind"),
        "records_selected": meta.get("records_selected"),
        "sources": sources,
    }


def command_predict(args) -> int:
    protocol = load_json(args.protocol)
    spec = spec_from_protocol(protocol)
    draws, meta = fetch_wclc_649(spec=spec)
    sealed_on = datetime.now(LOCAL_TZ).date().isoformat()
    prediction = make_prediction(
        draws,
        spec,
        protocol,
        target_draw_date=args.target_date,
        sealed_on_date=sealed_on,
        source_snapshot=source_summary(meta),
    )
    if not verify_prediction(prediction, protocol):
        raise RuntimeError("generated prediction failed internal verification")
    write_json(args.output, prediction)
    print(json.dumps({
        "output": str(args.output),
        "protocol_sha256": protocol_digest(protocol),
        "target_draw_date": prediction["target_draw_date"],
        "predicted_numbers": prediction["predicted_numbers"],
        "training_latest_draw_date": prediction["training"]["latest_draw_date"],
        "prediction_hash": prediction["prediction_hash"],
        "verified": True,
    }, indent=2))
    return 0


def _fetch_actual_by_date(spec):
    draws, _ = fetch_wclc_649(spec=spec)
    return {draw.draw_date: draw for draw in draws if draw.draw_date}


def command_score(args) -> int:
    protocol = load_json(args.protocol)
    prediction = load_json(args.prediction)
    if not verify_prediction(prediction, protocol):
        raise SystemExit("prediction verification failed")
    spec = spec_from_protocol(protocol)
    actual_by_date = _fetch_actual_by_date(spec)
    target = str(prediction["target_draw_date"])
    if target not in actual_by_date:
        payload = {"status": "pending", "target_draw_date": target}
        print(json.dumps(payload, indent=2))
        return 0 if args.allow_pending else 2
    score = score_prediction(prediction, actual_by_date[target], protocol)
    if not verify_score(score, protocol):
        raise RuntimeError("score failed internal verification")
    write_json(args.output, score)
    print(json.dumps({"status": "scored", "output": str(args.output), "target_draw_date": target, "hits": score["hits"], "verified": True}, indent=2))
    return 0


def command_score_ledger(args) -> int:
    protocol = load_json(args.protocol)
    spec = spec_from_protocol(protocol)
    actual_by_date = _fetch_actual_by_date(spec)
    args.scores_dir.mkdir(parents=True, exist_ok=True)
    scored = []
    pending = []
    for prediction_path in sorted(args.predictions_dir.glob("*.json")):
        prediction = load_json(prediction_path)
        if not verify_prediction(prediction, protocol):
            raise RuntimeError(f"prediction verification failed: {prediction_path}")
        target = str(prediction["target_draw_date"])
        score_path = args.scores_dir / f"{target}.json"
        if target not in actual_by_date:
            pending.append(target)
            continue
        score = score_prediction(prediction, actual_by_date[target], protocol)
        if not verify_score(score, protocol):
            raise RuntimeError(f"score verification failed: {target}")
        write_json(score_path, score)
        scored.append({"date": target, "hits": score["hits"]})
    print(json.dumps({"scored_or_verified": scored, "pending": pending}, indent=2))
    return 0


def command_evaluate(args) -> int:
    protocol = load_json(args.protocol)
    spec = spec_from_protocol(protocol)
    scores = [load_json(path) for path in sorted(args.scores_dir.glob("*.json"))] if args.scores_dir.exists() else []
    evaluation = evaluate_scores(scores, spec, protocol)
    write_json(args.output, evaluation, immutable=False)
    print(json.dumps(evaluation, indent=2, sort_keys=True))
    return 0


def command_verify(args) -> int:
    protocol = load_json(args.protocol)
    payload = load_json(args.artifact)
    schema = payload.get("schema")
    if "prospective_prediction" in str(schema):
        valid = verify_prediction(payload, protocol)
    elif "prospective_score" in str(schema):
        valid = verify_score(payload, protocol)
    else:
        raise SystemExit(f"unsupported artifact schema: {schema}")
    print(json.dumps({"artifact": str(args.artifact), "verified": bool(valid)}, indent=2))
    return 0 if valid else 1


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Lottery Forge prospective no-peeking ledger tools.")
    root.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    sub = root.add_subparsers(dest="command", required=True)

    predict = sub.add_parser("predict", help="Generate a sealed prediction for the next or specified future draw.")
    predict.add_argument("--target-date", help="ISO YYYY-MM-DD. Omit to choose the next scheduled draw after the latest official result.")
    predict.add_argument("--output", type=Path, required=True)
    predict.set_defaults(func=command_predict)

    score = sub.add_parser("score", help="Score one sealed prediction when its official outcome is available.")
    score.add_argument("--prediction", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    score.add_argument("--allow-pending", action="store_true")
    score.set_defaults(func=command_score)

    ledger = sub.add_parser("score-ledger", help="Score every pending sealed prediction whose official outcome exists.")
    ledger.add_argument("--predictions-dir", type=Path, required=True)
    ledger.add_argument("--scores-dir", type=Path, required=True)
    ledger.set_defaults(func=command_score_ledger)

    evaluate = sub.add_parser("evaluate", help="Evaluate scored predictions only at the frozen decision checkpoints.")
    evaluate.add_argument("--scores-dir", type=Path, required=True)
    evaluate.add_argument("--output", type=Path, required=True)
    evaluate.set_defaults(func=command_evaluate)

    verify = sub.add_parser("verify", help="Verify a prediction or score artifact hash and protocol binding.")
    verify.add_argument("--artifact", type=Path, required=True)
    verify.set_defaults(func=command_verify)
    return root


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
