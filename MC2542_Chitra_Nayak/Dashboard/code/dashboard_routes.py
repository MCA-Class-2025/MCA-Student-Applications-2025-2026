from pathlib import Path
import sys
import pandas as pd
from flask import Blueprint, jsonify, request

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from algorithms.merge_sort import merge_sort

dashboard_bp = Blueprint('dashboard', __name__)
DATASET_PATH = Path(__file__).resolve().parents[1] / 'datasets' / 'dataset_fusion.csv'

def load_data():
    return pd.read_csv(DATASET_PATH, low_memory=False)

def apply_filters(df):
    source = request.args.get('source', '').strip()
    year = request.args.get('year', '').strip()
    if source and source != 'All':
        df = df[df['source'].fillna('').astype(str).str.split('|', regex=False).apply(lambda items: source in [s.strip() for s in items])]
    if year and year != 'All':
        df = df[pd.to_numeric(df['year'], errors='coerce').eq(int(year))]
    return df

@dashboard_bp.route('/api/dashboard/overview', methods=['GET'])
def dashboard_overview():
    try:
        full = load_data()
        df = apply_filters(full)
        missing = df.isna() | df.astype(str).apply(lambda col: col.str.strip().eq(''))
        source_series = df['source'].dropna().astype(str).str.split('|', regex=False).explode().str.strip()
        sources = source_series[source_series.ne('')].value_counts()
        years = pd.to_numeric(df['year'], errors='coerce').dropna().astype(int).value_counts().sort_index()
        all_sources = full['source'].dropna().astype(str).str.split('|', regex=False).explode().str.strip()
        all_years = pd.to_numeric(full['year'], errors='coerce').dropna().astype(int)
        return jsonify(success=True, total_records=int(len(df)), total_columns=int(len(df.columns)),
                       duplicate_records=int(df.duplicated().sum()), missing_values=int(missing.sum().sum()),
                       missing_by_column={k:int(v) for k,v in missing.sum().sort_values(ascending=False).items()},
                       source_distribution={k:int(v) for k,v in sources.items()},
                       publication_trends={str(k):int(v) for k,v in years.items()},
                       filters={'sources':sorted(set(s for s in all_sources if s)),
                                'years':sorted(set(map(int, all_years)), reverse=True)},
                       filtered_records=int(len(df)), dataset_records=int(len(full)))
    except Exception as exc:
        return jsonify(success=False, error=str(exc)), 500

@dashboard_bp.route('/api/dashboard/records', methods=['GET'])
def dashboard_records():
    try:
        df = apply_filters(load_data())
        search = request.args.get('search', '').strip()
        page = max(request.args.get('page', 1, type=int), 1)
        page_size = min(max(request.args.get('page_size', 10, type=int), 1), 100)
        if search:
            df = df[df.fillna('').astype(str).apply(lambda col: col.str.contains(search, case=False, regex=False)).any(axis=1)]
        sort_by = request.args.get('sort_by', '')
        direction = request.args.get('sort_direction', 'asc')
        if sort_by in df.columns:
            if sort_by == 'year':
                years = pd.to_numeric(df['year'], errors='coerce')
                pairs = [(int(v), pos) for pos, v in enumerate(years) if pd.notna(v)]
                ordered = merge_sort(pairs)
                if direction == 'desc':
                    ordered.reverse()
                null_positions = [pos for pos, v in enumerate(years) if pd.isna(v)]
                df = df.iloc[[pos for _, pos in ordered] + null_positions]
            elif sort_by == 'citations':
                numeric = pd.to_numeric(df[sort_by], errors='coerce')
                df = df.assign(_sort=numeric).sort_values('_sort', ascending=direction!='desc', na_position='last', kind='stable').drop(columns='_sort')
            else:
                df = df.assign(_sort=df[sort_by].fillna('').astype(str).str.casefold()).sort_values('_sort', ascending=direction!='desc', kind='stable').drop(columns='_sort')
        total = len(df)
        records = df.iloc[(page-1)*page_size:page*page_size].astype(object).where(lambda f:pd.notna(f), None).to_dict(orient='records')
        return jsonify(success=True, records=records, columns=df.columns.tolist(), total=int(total), page=page,
                       page_size=page_size, total_pages=max(1, (total+page_size-1)//page_size))
    except Exception as exc:
        return jsonify(success=False, error=str(exc)), 500

@dashboard_bp.route('/api/dashboard/merge-sort', methods=['GET'])
def dashboard_merge_sort():
    try:
        years = pd.to_numeric(load_data()['year'], errors='coerce').dropna().astype(int).tolist()
        result = merge_sort(years)
        return jsonify(success=True, algorithm='Merge Sort', field='year', total_records=len(years),
                       original_years=years, sorted_years=result, sorting_successful=result==sorted(years),
                       time_complexity='O(n log n)', space_complexity='O(n)')
    except Exception as exc:
        return jsonify(success=False, error=str(exc)), 500

# Extended EDA and fusion analytics
import math
import numpy as np

ORIGINAL_DATASET_PATH = DATASET_PATH.parent / 'database.csv'
ANALYTICS_FIELDS = ['year', 'citations', 'download_count', 'vote_count',
                    'usability', 'file_count', 'size', 'cited_by_count',
                    'similarity_score', 'retrieved_paper_count']


def safe_number(value):
    return float(value) if pd.notna(value) and math.isfinite(float(value)) else None


def numeric_fields(df):
    result = pd.DataFrame(index=df.index)
    for field in ANALYTICS_FIELDS:
        if field in df.columns:
            values = pd.to_numeric(df[field], errors='coerce').replace([np.inf, -np.inf], np.nan)
            # Kaggle votes are not scholarly citations.
            if field == 'citations' and 'source' in df.columns:
                values = values.mask(df['source'].fillna('').str.contains('kaggle', case=False))
            result[field] = values
    return result


def summarize_dataset(df):
    missing = df.isna() | df.astype(str).apply(lambda col: col.str.strip().eq(''))
    cells = df.shape[0] * df.shape[1]
    return {
        'records': len(df), 'attributes': len(df.columns),
        'duplicate_records': int(df.duplicated().sum()),
        'missing_values': int(missing.sum().sum()),
        'missing_percentage': float(100 * missing.sum().sum() / cells) if cells else None,
        'missing_by_column': {k: int(v) for k, v in missing.sum().items()},
        'data_types': {k: str(v) for k, v in df.dtypes.items()},
        'unique_values': {k: int(df[k].mask(missing[k]).nunique()) for k in df.columns},
        'duplicate_identifiers': {
            k: int(df[k].mask(missing[k]).dropna().astype(str).str.strip().str.casefold().duplicated().sum())
            for k in ['Id', 'doi', 'eid', 'dataset_id'] if k in df.columns
        }
    }


def describe_numeric(values):
    s = values.dropna()
    if s.empty:
        return None
    q1, median, q3 = s.quantile([0.25, 0.5, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outside = (s < lower) | (s > upper)
    inside = s[~outside]
    counts, edges = np.histogram(s.to_numpy(), bins=min(12, max(1, int(np.sqrt(len(s))))))
    return {
        'count': len(s), 'mean': safe_number(s.mean()), 'median': safe_number(median),
        'std': safe_number(s.std()), 'min': safe_number(s.min()), 'max': safe_number(s.max()),
        'q1': safe_number(q1), 'q3': safe_number(q3), 'iqr': safe_number(iqr),
        'histogram': [{'start': float(edges[i]), 'end': float(edges[i+1]), 'count': int(n)}
                      for i, n in enumerate(counts)],
        'boxplot': {'min': safe_number(s.min()), 'q1': safe_number(q1),
                    'median': safe_number(median), 'q3': safe_number(q3), 'max': safe_number(s.max()),
                    'lower_whisker': safe_number(inside.min()), 'upper_whisker': safe_number(inside.max()),
                    'outliers': [float(v) for v in s[outside]]},
        'outliers': {'lower_bound': float(lower), 'upper_bound': float(upper),
                     'count': int(outside.sum()), 'percentage': float(100 * outside.mean()),
                     'interpretation': 'IQR flags unusual values; source verification is needed before classifying them as errors.'}
    }


def relationship(numeric, x, y):
    pair = numeric[[x, y]].dropna() if x in numeric and y in numeric else pd.DataFrame(columns=[x, y])
    correlation = pair[x].corr(pair[y]) if len(pair) >= 3 and pair[x].nunique() > 1 and pair[y].nunique() > 1 else None
    return {'x': x, 'y': y, 'count': len(pair), 'correlation': safe_number(correlation),
            'points': [{'x': float(a), 'y': float(b)} for a, b in pair.itertuples(index=False, name=None)]}


@dashboard_bp.route('/api/dashboard/analytics', methods=['GET'])
def dashboard_analytics():
    try:
        full = load_data()
        df = apply_filters(full)
        original = pd.read_csv(ORIGINAL_DATASET_PATH, low_memory=False)
        original = original.loc[:, ~original.columns.str.startswith('Unnamed:')]
        numeric = numeric_fields(df)
        stats = {k: describe_numeric(numeric[k]) for k in numeric.columns}
        stats = {k: v for k, v in stats.items() if v is not None}
        relationships = [relationship(numeric, 'download_count', 'vote_count'),
                         relationship(numeric, 'usability', 'download_count')]
        heat_fields = [k for k in ['download_count', 'vote_count', 'usability', 'file_count', 'size']
                       if k in numeric and numeric[k].count() >= 3 and numeric[k].nunique() > 1]
        heat_data = numeric[heat_fields]
        corr = heat_data.corr(min_periods=3)
        heatmap = [{'x': x, 'y': y, 'value': safe_number(corr.loc[x, y]),
                    'count': int((heat_data[x].notna() & heat_data[y].notna()).sum())}
                   for x in heat_fields for y in heat_fields]
        before, after = summarize_dataset(original), summarize_dataset(full)
        quality = summarize_dataset(df)
        new_fields = [k for k in full.columns if k not in original.columns]
        fusion_fields = [k for k in ['download_count', 'vote_count', 'usability', 'file_count', 'cited_by_count', 'similarity_score'] if k in full]
        coverage = [{'field': k, 'before': int(original[k].notna().sum()) if k in original else 0,
                     'after': int(full[k].notna().sum())} for k in fusion_fields]
        insights = [
            {'finding': 'The fused dataset contains more records.' if after['records'] > before['records'] else 'Record counts changed or remained equal.',
             'evidence': f"Original: {before['records']}; fused: {after['records']}.",
             'interpretation': 'The net difference measures dataset expansion, not the number of matched records.'},
            {'finding': 'Fusion expands the available schema.',
             'evidence': f"Original: {before['attributes']}; fused: {after['attributes']} columns.",
             'interpretation': 'New fields enable additional analysis; some are metadata or source-specific.'},
            {'finding': 'API-derived fields have limited coverage.',
             'evidence': '; '.join(f"{r['field']}: {r['after']} populated records" for r in coverage),
             'interpretation': 'Analyze each metric using records where it is available; missing does not mean zero.'}
        ]
        for rel in relationships:
            r = rel['correlation']
            insights.append({'finding': f"Relationship between {rel['x']} and {rel['y']}",
                             'evidence': f"Pearson r = {r:.3f}; paired records = {rel['count']}." if r is not None else f"Paired records = {rel['count']}; correlation unavailable.",
                             'interpretation': ('Positive association.' if r > 0 else 'Negative association.' if r < 0 else 'No linear association.') + ' This does not establish causation.' if r is not None else 'Insufficient variation or paired data to establish a relationship.'})
        return jsonify(success=True, quality=quality, descriptive_statistics=stats,
                       relationships=relationships, correlation_heatmap=heatmap,
                       correlation_fields=heat_fields, before_after={'before': before, 'after': after,
                       'new_fields': new_fields, 'net_records_added': after['records'] - before['records'],
                       'net_attributes_added': after['attributes'] - before['attributes']},
                       fusion_coverage=coverage, insights=insights,
                       comparison_scope='Full datasets; other analytics follow selected filters.',
                       consistency={'negative_counts': {k: int((numeric[k] < 0).sum()) for k in ['citations', 'download_count', 'vote_count', 'file_count', 'cited_by_count'] if k in numeric},
                                    'invalid_numeric_values': {k: int((df[k].notna() & pd.to_numeric(df[k], errors='coerce').isna()).sum()) for k in numeric},
                                    'usability_outside_0_1': int(((numeric['usability'] < 0) | (numeric['usability'] > 1)).sum()) if 'usability' in numeric else None})
    except Exception as exc:
        return jsonify(success=False, error=str(exc)), 500
