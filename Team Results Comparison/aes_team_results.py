import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

INPUT_PATH = r"C:\Git Repos\AES-Results-Scraping\Team Results Comparison\2026 Triple Crown NIT - TeamResults.csv"
NIT_CODES_PATH = r"C:\Git Repos\AES-Results-Scraping\Team Results Comparison\NIT_team_codes.csv"


def normalize_result(value: str) -> str:
	if value is None:
		return ""
	return value.strip().lower()


def is_canonical_team_code(team_code: str) -> bool:
	value = (team_code or "").strip().lower()
	return bool(re.match(r"^[a-z]\d{2}[a-z]+\d[a-z]{2}$", value))


def extract_age_group(team_code: str) -> str:
	value = (team_code or "").strip().lower()
	if len(value) >= 3 and value[0].isalpha() and value[1:3].isdigit():
		return value[:3]
	return ""


def normalize_code(value: str) -> str:
	return (value or "").strip().lower()


def load_team_code_set(path: Path) -> set[str]:
	if not path.exists():
		return set()
	with path.open("r", newline="", encoding="utf-8") as handle:
		reader = csv.DictReader(handle)
		return {normalize_code(row.get("Team Code")) for row in reader if row.get("Team Code")}


def aggregate_team_results(rows, group_key: str, opponent_code_set: set[str]):
	stats = defaultdict(
		lambda: {
			"team": "",
			"age_division": "",
			"team_code": "",
			"matches": 0,
			"wins": 0,
			"losses": 0,
			"other": 0,
			"same_age_matches": 0,
			"same_age_wins": 0,
			"same_age_losses": 0,
			"same_age_other": 0,
			"nit_matches": 0,
			"nit_wins": 0,
			"nit_losses": 0,
			"nit_other": 0,
			"nit_same_age_matches": 0,
			"nit_same_age_wins": 0,
			"nit_same_age_losses": 0,
			"nit_same_age_other": 0,
		}
	)

	for row in rows:
		key = (row.get(group_key) or "").strip()
		if not key:
			continue

		entry = stats[key]
		if not entry["team"]:
			entry["team"] = (row.get("Team") or "").strip()

		team_code = (row.get("Team Code") or "").strip()
		if (not entry["team_code"]) or (
			not is_canonical_team_code(entry["team_code"]) and is_canonical_team_code(team_code)
		):
			entry["team_code"] = team_code
			entry["age_division"] = extract_age_group(team_code)

		entry["matches"] += 1

		team_age = extract_age_group(row.get("Team Code"))
		opp_code = normalize_code(row.get("Opponent Team Code"))
		opp_age = extract_age_group(row.get("Opponent Team Code"))
		same_age = team_age and opp_age and team_age == opp_age
		in_nit_list = bool(opponent_code_set) and opp_code in opponent_code_set

		result = normalize_result(row.get("Result"))
		if result == "won":
			entry["wins"] += 1
			if same_age:
				entry["same_age_wins"] += 1
			if in_nit_list:
				entry["nit_wins"] += 1
				if same_age:
					entry["nit_same_age_wins"] += 1
		elif result == "lost":
			entry["losses"] += 1
			if same_age:
				entry["same_age_losses"] += 1
			if in_nit_list:
				entry["nit_losses"] += 1
				if same_age:
					entry["nit_same_age_losses"] += 1
		else:
			entry["other"] += 1
			if same_age:
				entry["same_age_other"] += 1
			if in_nit_list:
				entry["nit_other"] += 1
				if same_age:
					entry["nit_same_age_other"] += 1

		if same_age:
			entry["same_age_matches"] += 1
		if in_nit_list:
			entry["nit_matches"] += 1
			if same_age:
				entry["nit_same_age_matches"] += 1

	return stats


def write_csv(output_path: Path, stats, group_key: str):
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", newline="", encoding="utf-8") as handle:
		writer = csv.writer(handle)
		if group_key == "Team":
			writer.writerow(
				[
					"Team",
					"Team Code",
					"Age Division",
					"Matches",
					"Wins",
					"Losses",
					"Same-Age Matches",
					"Same-Age Wins",
					"Same-Age Losses",
					"NIT Matches",
					"NIT Wins",
					"NIT Losses",
					"NIT Same-Age Matches",
					"NIT Same-Age Wins",
					"NIT Same-Age Losses",
				]
			)
		else:
			writer.writerow(
				[
					group_key,
					"Team",
					"Team Code",
					"Age Division",
					"Matches",
					"Wins",
					"Losses",
					"Same-Age Matches",
					"Same-Age Wins",
					"Same-Age Losses",
					"NIT Matches",
					"NIT Wins",
					"NIT Losses",
					"NIT Same-Age Matches",
					"NIT Same-Age Wins",
					"NIT Same-Age Losses",
				]
			)

		for key, data in stats:
			if group_key == "Team":
				writer.writerow(
					[
						key,
						data["team_code"],
						data["age_division"],
						data["matches"],
						data["wins"],
						data["losses"],
						data["same_age_matches"],
						data["same_age_wins"],
						data["same_age_losses"],
						data["nit_matches"],
						data["nit_wins"],
						data["nit_losses"],
						data["nit_same_age_matches"],
						data["nit_same_age_wins"],
						data["nit_same_age_losses"],
					]
				)
			else:
				writer.writerow(
					[
						key,
						data["team"],
						data["team_code"],
						data["age_division"],
						data["matches"],
						data["wins"],
						data["losses"],
						data["same_age_matches"],
						data["same_age_wins"],
						data["same_age_losses"],
						data["nit_matches"],
						data["nit_wins"],
						data["nit_losses"],
						data["nit_same_age_matches"],
						data["nit_same_age_wins"],
						data["nit_same_age_losses"],
					]
				)


def print_summary(stats, group_key: str):
	print(f"Summary by {group_key}:")
	print(f"{'Key':<20} {'Team':<35} {'M':>4} {'W':>4} {'L':>4} {'SA M':>6} {'SA W':>6} {'SA L':>6}")
	print("-" * 105)
	for key, data in stats:
		team_name = data["team"][:34]
		print(
			f"{key:<20} {team_name:<35} {data['matches']:>4} {data['wins']:>4} {data['losses']:>4} "
			f"{data['same_age_matches']:>6} {data['same_age_wins']:>6} {data['same_age_losses']:>6}"
		)


def main() -> int:
	parser = argparse.ArgumentParser(description="Aggregate match results by team.")
	parser.add_argument(
		"--input",
		default=INPUT_PATH,
		help="Optional path to the match-results CSV.",
	)
	parser.add_argument(
		"--group",
		default="Team",
		choices=["Team", "Team Code"],
		help="Field to group by.",
	)
	parser.add_argument(
		"--nit-codes",
		default=NIT_CODES_PATH,
		help="Optional path to CSV with the list of opponent team codes (Team Code column).",
	)
	parser.add_argument(
		"--output",
		default=None,
		help="Optional output CSV path. Defaults to '<input>_team_summary.csv'.",
	)

	args = parser.parse_args()
	input_path = Path(args.input)
	if not input_path.exists():
		raise FileNotFoundError(f"Input file not found: {input_path}")

	nit_codes = load_team_code_set(Path(args.nit_codes))
	with input_path.open("r", newline="", encoding="utf-8") as handle:
		reader = csv.DictReader(handle)
		stats_map = aggregate_team_results(reader, args.group, nit_codes)

	stats_list = sorted(
		stats_map.items(),
		key=lambda item: (-item[1]["wins"], -item[1]["matches"], item[0].lower()),
	)

	print_summary(stats_list, args.group)

	other_total = sum(data["other"] for _, data in stats_list)
	same_age_other_total = sum(data["same_age_other"] for _, data in stats_list)
	nit_other_total = sum(data["nit_other"] for _, data in stats_list)
	nit_same_age_other_total = sum(data["nit_same_age_other"] for _, data in stats_list)
	if other_total:
		print(f"\nNote: {other_total} matches have non Win/Loss results (e.g., Tie, Undecided).")
	if same_age_other_total:
		print(
			"Note:"
			f" {same_age_other_total} same-age matches have non Win/Loss results (e.g., Tie, Undecided)."
		)
	if nit_other_total:
		print(
			"Note:"
			f" {nit_other_total} NIT-list matches have non Win/Loss results (e.g., Tie, Undecided)."
		)
	if nit_same_age_other_total:
		print(
			"Note:"
			f" {nit_same_age_other_total} NIT same-age matches have non Win/Loss results"
			" (e.g., Tie, Undecided)."
		)

	output_path = Path(args.output) if args.output else input_path.with_name(f"{input_path.stem}_team_summary.csv")
	write_csv(output_path, stats_list, args.group)
	print(f"\nWrote summary CSV to: {output_path}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
