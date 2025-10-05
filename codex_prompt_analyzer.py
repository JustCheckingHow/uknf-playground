#!/usr/bin/env python3
"""
Codex Prompt Analyzer
Analyzes Codex code agent session logs from .jsonl files.
"""

import json
import sys
import csv
from pathlib import Path
afrom datetime import datetime, timedelta
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np


def parse_jsonl_file(file_path):
    """Parse a JSONL file and extract relevant data."""
    events = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    events.append(event)
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line in {file_path}: {e}")
                    continue
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return events


def extract_token_events(events):
    """Extract token count events with timestamps (converted to GMT+2)."""
    token_events = []
    for event in events:
        if (event.get('type') == 'event_msg' and 
            event.get('payload', {}).get('type') == 'token_count'):
            
            timestamp_str = event.get('timestamp')
            token_info = event.get('payload', {}).get('info')
            
            # Skip if token_info is None
            if not token_info:
                continue
                
            last_usage = token_info.get('last_token_usage', {})
            
            if timestamp_str and last_usage:
                try:
                    # Parse UTC timestamp and convert to GMT+2
                    timestamp_utc = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    timestamp_gmt2 = timestamp_utc + timedelta(hours=2)
                    output_tokens = last_usage.get('output_tokens', 0)
                    token_events.append({
                        'timestamp': timestamp_gmt2,
                        'output_tokens': output_tokens,
                        'last_usage': last_usage
                    })
                except Exception as e:
                    print(f"Warning: Failed to parse timestamp {timestamp_str}: {e}")
    return token_events


def count_interactions(events):
    """Count the number of user<->system interactions in a session."""
    # An interaction is counted when we see a complete turn
    # We'll count response_item events with type "message" as complete interactions
    interaction_count = 0
    for event in events:
        if event.get('type') == 'response_item':
            payload = event.get('payload', {})
            if payload.get('type') == 'message' and payload.get('role') == 'assistant':
                interaction_count += 1
    
    # If no message events found, use token_count events as proxy
    if interaction_count == 0:
        token_count_events = sum(1 for e in events 
                                if e.get('type') == 'event_msg' 
                                and e.get('payload', {}).get('type') == 'token_count')
        # Approximate: each token count usually represents one interaction
        interaction_count = max(1, token_count_events)
    
    return interaction_count


def analyze_sessions(folders):
    """Analyze all session files in the given folders."""
    all_token_events = []
    session_data = []
    
    for folder_path in folders:
        folder = Path(folder_path)
        if not folder.exists():
            print(f"Warning: Folder {folder} does not exist")
            continue
        
        jsonl_files = list(folder.glob('*.jsonl'))
        print(f"Found {len(jsonl_files)} .jsonl files in {folder}")
        
        for jsonl_file in jsonl_files:
            print(f"Processing {jsonl_file.name}...")
            events = parse_jsonl_file(jsonl_file)
            
            # Extract token events for timeline
            token_events = extract_token_events(events)
            all_token_events.extend(token_events)
            
            # Count interactions for this session
            interactions = count_interactions(events)
            
            # Sum total output tokens for this session
            total_tokens = sum(te['output_tokens'] for te in token_events)
            
            session_data.append({
                'session_name': jsonl_file.stem,
                'interactions': interactions,
                'total_tokens': total_tokens,
                'token_events': token_events
            })
            
            print(f"  - {len(token_events)} token events, {interactions} interactions, {total_tokens} total output tokens")
    
    return all_token_events, session_data


def save_timeline_csv(token_events, output_dir):
    """Save timeline data to CSV for Canva (aggregated by 30-minute intervals)."""
    if not token_events:
        return
    
    # Sort by timestamp
    token_events = sorted(token_events, key=lambda x: x['timestamp'])
    
    # Aggregate by 30-minute intervals
    from collections import defaultdict
    interval_buckets = defaultdict(int)
    
    for te in token_events:
        # Round down to nearest 30-minute interval
        ts = te['timestamp']
        # Calculate minutes within the hour, then round down to nearest 30
        minutes_in_hour = ts.minute
        interval_minute = (minutes_in_hour // 30) * 30  # Will be either 0 or 30
        # Create new timestamp at the interval boundary
        interval_ts = ts.replace(minute=interval_minute, second=0, microsecond=0)
        
        interval_buckets[interval_ts] += te['output_tokens']
    
    # Sort by timestamp
    sorted_intervals = sorted(interval_buckets.items())
    
    csv_path = output_dir / 'timeline_data.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Time (DD HH:MM)', 'Output Tokens'])
        for ts, tokens in sorted_intervals:
            writer.writerow([
                ts.strftime('%d %H:%M'),
                tokens
            ])
    print(f"Saved timeline data (30-min intervals) to {csv_path}")


def save_interaction_csv(session_data, output_dir):
    """Save interaction data to CSV for Canva."""
    if not session_data:
        return
    
    csv_path = output_dir / 'interactions_data.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Session', 'Interaction Count'])
        for session in session_data:
            writer.writerow([
                session['session_name'],
                session['interactions']
            ])
    print(f"Saved interaction data to {csv_path}")


def save_tokens_csv(session_data, output_dir):
    """Save total tokens data to CSV for Canva."""
    if not session_data:
        return
    
    csv_path = output_dir / 'tokens_per_session_data.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Session', 'Total Output Tokens'])
        for session in session_data:
            if session['total_tokens'] > 0:  # Only include sessions with tokens
                writer.writerow([
                    session['session_name'],
                    session['total_tokens']
                ])
    print(f"Saved tokens per session data to {csv_path}")


def save_scatter_csv(session_data, output_dir):
    """Save scatter plot data to CSV for Canva (sorted by time)."""
    if not session_data:
        return
    
    # Prepare data with timestamps
    rows = []
    for session in session_data:
        if session['total_tokens'] > 0 and session['token_events']:
            # Get first timestamp from token events (already in GMT+2)
            first_timestamp = min(te['timestamp'] for te in session['token_events'])
            rows.append({
                'timestamp': first_timestamp,
                'tokens': session['total_tokens'],
                'interactions': session['interactions']
            })
    
    # Sort by timestamp
    rows.sort(key=lambda x: x['timestamp'])
    
    csv_path = output_dir / 'session_scatter_data.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Session Start Time', 'Total Output Tokens', 'Number of Interactions'])
        for row in rows:
            writer.writerow([
                row['timestamp'].strftime('%d %H:%M'),
                row['tokens'],
                row['interactions']
            ])
    print(f"Saved scatter plot data to {csv_path}")


def create_timeline_chart(token_events, output_dir):
    """Create timeline of output tokens (aggregated by 30-minute intervals)."""
    if not token_events:
        print("No token events to plot")
        return
    
    # Sort by timestamp
    token_events = sorted(token_events, key=lambda x: x['timestamp'])
    
    # Aggregate by 30-minute intervals
    interval_buckets = defaultdict(int)
    
    for te in token_events:
        # Round down to nearest 30-minute interval
        ts = te['timestamp']
        # Calculate minutes within the hour, then round down to nearest 30
        minutes_in_hour = ts.minute
        interval_minute = (minutes_in_hour // 30) * 30  # Will be either 0 or 30
        # Create new timestamp at the interval boundary
        interval_ts = ts.replace(minute=interval_minute, second=0, microsecond=0)
        
        interval_buckets[interval_ts] += te['output_tokens']
    
    # Sort by timestamp
    sorted_intervals = sorted(interval_buckets.items())
    timestamps = [ts for ts, _ in sorted_intervals]
    output_tokens = [tokens for _, tokens in sorted_intervals]
    
    plt.figure(figsize=(14, 6))
    plt.plot(timestamps, output_tokens, marker='o', linestyle='-', markersize=5, alpha=0.7, linewidth=2)
    plt.xlabel('Time (GMT+2)', fontsize=12)
    plt.ylabel('Output Tokens (30-min intervals)', fontsize=12)
    plt.title('Timeline of Output Tokens (30-minute Aggregation, GMT+2)', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # Format x-axis
    plt.gcf().autofmt_xdate()
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %H:%M'))
    
    plt.tight_layout()
    output_path = output_dir / 'timeline_output_tokens.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved timeline chart to {output_path}")
    plt.close()


def create_interaction_histogram(session_data, output_dir):
    """Create histogram of interaction counts per session."""
    if not session_data:
        print("No interaction data to plot")
        return
    
    session_interactions = [s['interactions'] for s in session_data]
    
    plt.figure(figsize=(10, 6))
    
    # Create histogram
    bins = range(min(session_interactions), max(session_interactions) + 2)
    plt.hist(session_interactions, bins=bins, edgecolor='black', alpha=0.7, color='steelblue')
    
    plt.xlabel('Number of Interactions per Session', fontsize=12)
    plt.ylabel('Frequency (Number of Sessions)', fontsize=12)
    plt.title('Distribution of Interaction Counts Across Sessions', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3, axis='y')
    
    # Add mean line
    mean_interactions = np.mean(session_interactions)
    plt.axvline(mean_interactions, color='red', linestyle='--', linewidth=2, 
                label=f'Mean: {mean_interactions:.1f}')
    plt.legend()
    
    plt.tight_layout()
    output_path = output_dir / 'interaction_histogram.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved interaction histogram to {output_path}")
    plt.close()


def create_tokens_histogram(session_data, output_dir):
    """Create histogram of total output tokens per session."""
    if not session_data:
        print("No token data to plot")
        return
    
    # Filter out zero-token sessions
    session_total_tokens = [s['total_tokens'] for s in session_data if s['total_tokens'] > 0]
    
    if not session_total_tokens:
        print("No non-zero token sessions to plot")
        return
    
    plt.figure(figsize=(10, 6))
    
    # Create histogram with automatic binning
    plt.hist(session_total_tokens, bins=20, edgecolor='black', alpha=0.7, color='forestgreen')
    
    plt.xlabel('Total Output Tokens per Session', fontsize=12)
    plt.ylabel('Frequency (Number of Sessions)', fontsize=12)
    plt.title('Distribution of Output Tokens Across Sessions', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3, axis='y')
    
    # Add statistics
    mean_tokens = np.mean(session_total_tokens)
    median_tokens = np.median(session_total_tokens)
    plt.axvline(mean_tokens, color='red', linestyle='--', linewidth=2, 
                label=f'Mean: {mean_tokens:.0f}')
    plt.axvline(median_tokens, color='orange', linestyle='--', linewidth=2, 
                label=f'Median: {median_tokens:.0f}')
    plt.legend()
    
    plt.tight_layout()
    output_path = output_dir / 'tokens_per_session_histogram.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved tokens histogram to {output_path}")
    plt.close()


def create_scatter_plot(session_data, output_dir):
    """Create scatter plot: time vs tokens with bubble size in log scale for interactions."""
    if not session_data:
        print("No session data to plot")
        return
    
    # Prepare data
    timestamps = []
    tokens = []
    interactions = []
    
    for session in session_data:
        if session['total_tokens'] > 0 and session['token_events']:
            # Get first timestamp from token events (already in GMT+2)
            first_timestamp = min(te['timestamp'] for te in session['token_events'])
            timestamps.append(first_timestamp)
            tokens.append(session['total_tokens'])
            interactions.append(session['interactions'])
    
    if not timestamps:
        print("No valid session data for scatter plot")
        return
    
    plt.figure(figsize=(14, 7))
    
    # Create scatter plot with log scale size based on interactions
    # Use log scale for bubble sizes: size = base_size * log(interactions + 1)
    base_size = 100
    sizes = [base_size * np.log10(i + 1) * 50 for i in interactions]
    
    scatter = plt.scatter(timestamps, tokens, s=sizes, alpha=0.6, c=interactions, 
                         cmap='viridis', edgecolors='black', linewidth=0.5)
    
    plt.xlabel('Session Start Time (GMT+2)', fontsize=12)
    plt.ylabel('Total Output Tokens', fontsize=12)
    plt.title('Session Analysis: Time vs Output Tokens (bubble size = log(interactions))', 
              fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # Add colorbar
    cbar = plt.colorbar(scatter)
    cbar.set_label('Number of Interactions', fontsize=11)
    
    # Format x-axis
    plt.gcf().autofmt_xdate()
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %H:%M'))
    
    # Add legend for bubble sizes (showing actual interaction counts)
    legend_sizes = [min(interactions), int(np.median(interactions)), max(interactions)]
    legend_bubbles = []
    legend_labels = []
    for size in legend_sizes:
        bubble_size = base_size * np.log10(size + 1) * 50
        legend_bubbles.append(plt.scatter([], [], s=bubble_size, c='gray', alpha=0.6, edgecolors='black'))
        legend_labels.append(f'{size} interactions')
    
    plt.legend(legend_bubbles, legend_labels, scatterpoints=1, frameon=True, 
              labelspacing=2, title='Bubble Size (log scale)', loc='upper left', fontsize=10)
    
    plt.tight_layout()
    output_path = output_dir / 'session_scatter_plot.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved scatter plot to {output_path}")
    plt.close()


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python codex_prompt_analyzer.py <folder1> [folder2] ...")
        print("  Analyzes .jsonl session files in the specified folders")
        sys.exit(1)
    
    folders = sys.argv[1:]
    
    print(f"Analyzing sessions in {len(folders)} folder(s)...")
    print()
    
    # Analyze all sessions
    all_token_events, session_data = analyze_sessions(folders)
    
    if not all_token_events and not session_data:
        print("No data found to analyze")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path('charts')
    output_dir.mkdir(exist_ok=True)
    print()
    print(f"Creating charts and CSV files in {output_dir}...")
    print()
    
    # Save CSV files for Canva
    save_timeline_csv(all_token_events, output_dir)
    save_interaction_csv(session_data, output_dir)
    save_tokens_csv(session_data, output_dir)
    save_scatter_csv(session_data, output_dir)
    print()
    
    # Generate charts
    create_timeline_chart(all_token_events, output_dir)
    create_interaction_histogram(session_data, output_dir)
    create_tokens_histogram(session_data, output_dir)
    create_scatter_plot(session_data, output_dir)
    
    # Print summary statistics
    print()
    print("=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    print(f"Total sessions analyzed: {len(session_data)}")
    print(f"Total token events: {len(all_token_events)}")
    if session_data:
        session_interactions = [s['interactions'] for s in session_data]
        print(f"Mean interactions per session: {np.mean(session_interactions):.2f}")
        print(f"Median interactions per session: {np.median(session_interactions):.0f}")
        print(f"Min/Max interactions: {min(session_interactions)} / {max(session_interactions)}")
        
        valid_tokens = [s['total_tokens'] for s in session_data if s['total_tokens'] > 0]
        if valid_tokens:
            print(f"Mean output tokens per session: {np.mean(valid_tokens):.0f}")
            print(f"Median output tokens per session: {np.median(valid_tokens):.0f}")
            print(f"Total output tokens: {sum(valid_tokens)}")
    print("=" * 60)
    print()
    print("Files created:")
    print(f"  Charts: {output_dir}/")
    print(f"    - timeline_output_tokens.png")
    print(f"    - interaction_histogram.png")
    print(f"    - tokens_per_session_histogram.png")
    print(f"    - session_scatter_plot.png")
    print(f"  CSV Data (for Canva):")
    print(f"    - timeline_data.csv")
    print(f"    - interactions_data.csv")
    print(f"    - tokens_per_session_data.csv")
    print(f"    - session_scatter_data.csv")


if __name__ == '__main__':
    main()