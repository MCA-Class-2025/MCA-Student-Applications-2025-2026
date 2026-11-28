
def merge_sort(arr):
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2

    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])

    return merge(left, right)


def merge(left, right):
    result = []
    i = 0
    j = 0

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])

    return result


if __name__ == "__main__":
    from pathlib import Path
    import pandas as pd

    dataset_path = (
        Path(__file__).resolve().parent.parent
        / "backend" / "datasets" / "dataset_fusion.csv"
    )

    df = pd.read_csv(dataset_path, low_memory=False)

    publication_years = (
        pd.to_numeric(df["year"], errors="coerce")
        .dropna()
        .astype(int)
        .tolist()
    )

    sorted_years = merge_sort(publication_years)

    print("Total Years:", len(publication_years))
    print("First 20 Original Years:", publication_years[:20])
    print("First 20 Sorted Years:", sorted_years[:20])
    print("Last 20 Sorted Years:", sorted_years[-20:])
    print("Sorting Successful:", sorted_years == sorted(publication_years))
