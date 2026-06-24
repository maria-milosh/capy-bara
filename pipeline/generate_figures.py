import json
import seaborn as sns
import typer
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import definitions



def parse_cbsa(config_loc: str) -> definitions.CBSA:
    with open(config_loc) as f:
        data = json.load(f)
    return definitions.CBSA.parse_raw(data)


def output_name_parts(filename: str):
    output_stem = Path(filename).stem
    for suffix in ("_connected", "_orig"):
        if output_stem.endswith(suffix):
            output_stem = output_stem.removesuffix(suffix)

    output_stem = output_stem.removesuffix("_vintage")
    _, study_area_and_dates = output_stem.split("_in_", 1)
    study_area_identity, geography_year, month, vintage_year = (
        study_area_and_dates.rsplit("_", 3)
    )
    return study_area_identity, geography_year, f"{month}_{vintage_year}"


def definition_json_for_output(filename: str) -> str:
    study_area_identity, _, definition_vintage = output_name_parts(filename)
    definition_stem = f"{study_area_identity}_{definition_vintage}"
    return f"study_areas/definitions/{definition_stem}.json"



def enrich_metrics(df: pd.DataFrame) -> pd.DataFrame:
    cbsa_infos = (
        df["filename"]
        .apply(definition_json_for_output)
        .apply(parse_cbsa)
    )
    df["definition_month_year"] = df["filename"].apply(
        lambda x: output_name_parts(x)[2])

    df["year"] = df["filename"].apply(
        lambda x: int(output_name_parts(x)[1])
    )
    df["cbsa_title"] = cbsa_infos.apply(lambda x: x.cbsa_title)
    df["cbsa_code"] = cbsa_infos.apply(lambda x: x.cbsa_code)
    df["total_population_2020"] = cbsa_infos.apply(lambda x: x.total_population)
    return df


def main(
    filename: str = "outputs/tracts_in_cbsa_2020-2010-2000-1990-1980_years_march_2020_vintage/white_poc.csv",
    n: int = 10,
    prefix: str = "white_poc_cbsa_tracts_march_2020",
):
    output_dir = f"{Path(filename).parent}/"
    print(f"Saving figures to {output_dir}figures/")
    Path(output_dir + "/figures").mkdir(exist_ok=True)

    df = enrich_metrics(pd.read_csv(filename))
    df = df.sort_values("total_population_2020", ascending=False)

    for month_year in set(df["definition_month_year"]):
        month_year_df = df[df["definition_month_year"] == month_year]

        top_n_metros = set(month_year_df["cbsa_title"].drop_duplicates()[:n])
        top_n_df = month_year_df[
            month_year_df["cbsa_title"].apply(lambda x: x in top_n_metros)
        ].sort_values(["cbsa_title", "year"])

        sns.set_theme(rc={"figure.figsize": (10, 4)})
        for metric in [
            "edge_lam_1_angle_1",
            "half_edge_lam_1_angle_1",
            "edge_lam_1_angle_2",
            "half_edge_lam_1_angle_2",
            "moran",
            "dissimilarity",
            "gini",
        ]:
            ax = sns.lineplot(
                data=top_n_df,
                y=metric,
                x="year",
                hue="cbsa_title")
            ax.set_xticks(sorted(top_n_df["year"].unique()))
            plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
            plt.tight_layout()
            plt.savefig(f"{output_dir}/figures/{prefix}_{metric}.png")
            plt.close()


if __name__ == "__main__":
    typer.run(main)
