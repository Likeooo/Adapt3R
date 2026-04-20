from argparse import ArgumentParser
import json
from pathlib import Path


def compute_success_rate(progress):
    successes = progress.get("successes")
    if isinstance(successes, list) and len(successes) > 0:
        # Cast booleans/numbers to float to support mixed legacy formats.
        return sum(float(x) for x in successes) / len(successes)

    per_env_keys = ("per_env_success_rates", "per_env_success")
    for key in per_env_keys:
        per_env = progress.get(key)
        if isinstance(per_env, dict) and len(per_env) > 0:
            values = [float(v) for v in per_env.values()]
            return sum(values) / len(values)

    raise ValueError("Cannot infer overall success rate from progress.json")


def compute_task_count(progress):
    dict_keys = (
        "per_env_success_rates",
        "per_env_success",
        "per_env_rewards",
        "per_env_metrics",
    )
    for key in dict_keys:
        value = progress.get(key)
        if isinstance(value, dict) and len(value) > 0:
            return len(value)

    list_keys = ("per_env_any_success", "per_env_solved")
    for key in list_keys:
        value = progress.get(key)
        if isinstance(value, list) and len(value) > 0:
            return len(value)

    return None


def summarize_progress(progress_path):
    with progress_path.open("r") as f:
        progress = json.load(f)

    task_count = compute_task_count(progress)
    success_rate = compute_success_rate(progress)
    episode_count = len(progress.get("successes", []))
    return {
        "file": progress_path,
        "tasks_tested": task_count,
        "overall_success_rate": success_rate,
        "episodes": episode_count,
    }


def print_single_summary(summary):
    print(f"file: {summary['file']}")
    if summary["tasks_tested"] is None:
        print("tasks_tested: unknown")
    else:
        print(f"tasks_tested: {summary['tasks_tested']}")
    success_rate = summary["overall_success_rate"]
    print(f"overall_success_rate: {success_rate:.6f} ({success_rate * 100:.2f}%)")
    if summary["episodes"] > 0:
        print(f"episodes: {summary['episodes']}")


def collect_batch_summaries(root_dir):
    root_dir = root_dir.resolve()
    progress_files = sorted(root_dir.rglob("progress.json"))
    grouped = []
    for progress_path in progress_files:
        if not progress_path.is_file():
            continue

        rel = progress_path.relative_to(root_dir)
        # Expected folder shape: exp_name/variant_name/.../progress.json
        if len(rel.parts) < 3:
            continue

        summary = summarize_progress(progress_path)
        summary["exp_name"] = rel.parts[0]
        summary["variant_name"] = rel.parts[1]
        summary["run"] = "/".join(rel.parts[2:-1]) if len(rel.parts) > 3 else "."
        grouped.append(summary)

    grouped.sort(key=lambda x: (x["exp_name"], x["variant_name"], x["run"], str(x["file"])))
    return grouped


def print_batch_summaries(summaries, root_dir):
    print(f"scan_root: {root_dir}")
    print(f"progress_files_found: {len(summaries)}")

    current_group = None
    for summary in summaries:
        group = (summary["exp_name"], summary["variant_name"])
        if group != current_group:
            if current_group is not None:
                print("")
            print(f"[{summary['exp_name']} / {summary['variant_name']}]")
            current_group = group

        task_text = "unknown" if summary["tasks_tested"] is None else str(summary["tasks_tested"])
        success_rate = summary["overall_success_rate"]
        print(
            f"run: {summary['run']} | tasks_tested: {task_text} | "
            f"overall_success_rate: {success_rate:.6f} ({success_rate * 100:.2f}%) | "
            f"episodes: {summary['episodes']} | file: {summary['file']}"
        )


def main():
    parser = ArgumentParser(description="Summarize progress.json evaluation results")
    parser.add_argument(
        "progress_json",
        nargs="?",
        help="Path to a single progress.json file. If omitted, run batch mode.",
    )
    parser.add_argument(
        "--root",
        default="experiments/evaluate/libero/libero_90",
        help="Batch mode scan root. Expected layout: exp_name/variant_name/...",
    )
    args = parser.parse_args()

    if args.progress_json is not None:
        summary = summarize_progress(Path(args.progress_json))
        print_single_summary(summary)
    else:
        root_dir = Path(args.root)
        summaries = collect_batch_summaries(root_dir)
        print_batch_summaries(summaries, root_dir)


if __name__ == "__main__":
    main()