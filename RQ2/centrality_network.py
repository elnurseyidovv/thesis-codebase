import os
import re
import json
import logging
import networkx as nx
from github import Github
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
from time import sleep
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File paths for saving/loading
CLASS_TO_FILE_JSON = "class_to_file.json"
GRAPH_COMMITS_GPICKLE = "graph_commits.gpickle"
GRAPH_FULL_GPICKLE = "graph_full.gpickle"
PROCESSED_FILES_JSON = "processed_files.json"
COMMIT_CHECKPOINT_JSON = "commit_checkpoint.json"
OUTPUT_CSV = "android_centrality.csv"


def check_rate_limit(g):
    """Check GitHub API rate limit and sleep if necessary."""
    try:
        rate_limit = g.get_rate_limit()
        if rate_limit.core.remaining < 10:
            reset_time = rate_limit.core.reset.timestamp()
            current_time = datetime.now().timestamp()
            sleep_time = reset_time - current_time + 1
            logger.info(f"Rate limit low. Sleeping for {sleep_time:.1f} seconds.")
            sleep(sleep_time)
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")


def get_classes_from_file(file_path):
    """Extract class names from a Java file using regex."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        package_pattern = r'^\s*package\s+([\w\.]+)\s*;'
        class_pattern = r'^\s*(?:public|private|protected)?\s*(class|interface|enum|@interface)\s+(\w+)\s+'
        package_match = re.search(package_pattern, content, re.MULTILINE)
        package = package_match.group(1) if package_match else ''
        class_matches = re.findall(class_pattern, content, re.MULTILINE)
        return [f"{package}.{class_name}" if package else class_name for class_name in class_matches]
    except (IOError, UnicodeDecodeError) as e:
        logger.error(f"Error reading {file_path}: {e}")
        return []


def get_imports(file_path):
    """Extract import statements from a Java file using regex."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        import_pattern = r'^\s*import\s+([\w\.]+)\s*;'
        imports = re.findall(import_pattern, content, re.MULTILINE)
        return [imp for imp in imports if not imp.startswith(('java.', 'javax.', 'org.junit', 'org.mockito'))]
    except (IOError, UnicodeDecodeError) as e:
        logger.error(f"Error reading {file_path}: {e}")
        return []


def build_class_to_file_mapping(root_dir, max_workers=4):
    """Build a mapping of class names to file paths, with parallel processing."""
    if os.path.exists(CLASS_TO_FILE_JSON):
        try:
            with open(CLASS_TO_FILE_JSON, 'r') as f:
                logger.info(f"Loading class-to-file mapping from {CLASS_TO_FILE_JSON}")
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load {CLASS_TO_FILE_JSON}: {e}. Rebuilding mapping.")

    class_to_file = {}
    java_files = [os.path.join(subdir, file) for subdir, _, files in os.walk(root_dir)
                  for file in files if file.endswith('.java')]
    logger.info(f"Found {len(java_files)} Java files to process")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(get_classes_from_file, file_path): file_path
                          for file_path in java_files}
        for future in future_to_file:
            file_path = future_to_file[future]
            try:
                classes = future.result()
                for cls in classes:
                    class_to_file[cls] = file_path
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")

    try:
        with open(CLASS_TO_FILE_JSON, 'w') as f:
            json.dump(class_to_file, f)
        logger.info(f"Saved class-to-file mapping to {CLASS_TO_FILE_JSON}")
    except IOError as e:
        logger.error(f"Error saving {CLASS_TO_FILE_JSON}: {e}")

    return class_to_file


def process_commits(g, repo, root_dir, max_commits=1000):
    if os.path.exists(GRAPH_COMMITS_GPICKLE):
        try:
            G = nx.read_gpickle(GRAPH_COMMITS_GPICKLE)
            logger.info(f"Loaded commit graph from {GRAPH_COMMITS_GPICKLE}")
            with open(COMMIT_CHECKPOINT_JSON, 'r') as f:
                checkpoint = json.load(f)
            start_index = checkpoint.get("last_processed", 0) + 1
        except (FileNotFoundError, json.JSONDecodeError, nx.NetworkXError) as e:
            logger.warning(f"Could not load commit graph or checkpoint: {e}. Starting from scratch.")
            G = nx.DiGraph()
            start_index = 0
    else:
        G = nx.DiGraph()
        start_index = 0

    try:
        commits = list(repo.get_commits()[:max_commits])
        total_commits = len(commits)
        logger.info(f"Processing up to {total_commits} commits")
    except Exception as e:
        logger.error(f"Error fetching commits: {e}")
        return G

    for i in range(start_index, total_commits):
        if i % 100 == 0:
            check_rate_limit(g)
        try:
            commit = commits[i]
            if commit.author is None or not hasattr(commit.author, 'login'):
                logger.warning(f"Commit {commit.sha} has no valid author. Skipping.")
                continue
            author = commit.author.login
            files_changed = [f.filename for f in commit.files if f.filename.endswith('.java')]
            for f in files_changed:
                full_path = os.path.join(root_dir, f)
                if os.path.exists(full_path):
                    G.add_edge(author, full_path)
            # Co-changing files
            for j, f1 in enumerate(files_changed):
                for f2 in files_changed[j + 1:]:
                    full_path1 = os.path.join(root_dir, f1)
                    full_path2 = os.path.join(root_dir, f2)
                    if os.path.exists(full_path1) and os.path.exists(full_path2):
                        G.add_edge(full_path1, full_path2)
                        G.add_edge(full_path2, full_path1)
            if (i + 1) % 100 == 0:
                try:
                    nx.write_gpickle(G, GRAPH_COMMITS_GPICKLE)
                    with open(COMMIT_CHECKPOINT_JSON, 'w') as f:
                        json.dump({"last_processed": i}, f)
                    logger.info(f"Processed {i + 1} commits, saved checkpoint")
                except Exception as e:
                    logger.error(f"Error saving commit checkpoint: {e}")
        except Exception as e:
            logger.error(f"Error processing commit {i}: {e}")
            continue

    # Final save
    try:
        nx.write_gpickle(G, GRAPH_COMMITS_GPICKLE)
        with open(COMMIT_CHECKPOINT_JSON, 'w') as f:
            json.dump({"last_processed": total_commits - 1}, f)
        logger.info("Completed commit processing and saved final graph")
    except Exception as e:
        logger.error(f"Error saving final commit graph: {e}")

    return G


def add_dependency_edges(G, class_to_file, root_dir):
    """Add dependency edges to the graph based on file imports."""
    if os.path.exists(PROCESSED_FILES_JSON):
        try:
            with open(PROCESSED_FILES_JSON, 'r') as f:
                processed_files = set(json.load(f))
            logger.info(f"Loaded processed files from {PROCESSED_FILES_JSON}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load {PROCESSED_FILES_JSON}: {e}. Starting from scratch.")
            processed_files = set()
    else:
        processed_files = set()

    all_files = [node for node in G.nodes() if node.endswith('.java')]
    logger.info(f"Processing dependencies for {len(all_files)} files")

    for i, file in enumerate(all_files):
        if file in processed_files:
            continue
        try:
            imports = get_imports(file)
            dependencies = [class_to_file[imp] for imp in imports if imp in class_to_file]
            for dep in dependencies:
                if os.path.exists(dep):
                    G.add_edge(file, dep)
            processed_files.add(file)
            if (i + 1) % 100 == 0:
                try:
                    with open(PROCESSED_FILES_JSON, 'w') as f:
                        json.dump(list(processed_files), f)
                    nx.write_gpickle(G, GRAPH_FULL_GPICKLE)
                    logger.info(f"Processed {i + 1} files for dependencies, saved checkpoint")
                except Exception as e:
                    logger.error(f"Error saving dependency checkpoint: {e}")
        except Exception as e:
            logger.error(f"Error processing {file}: {e}")
            continue

    # Final save
    try:
        with open(PROCESSED_FILES_JSON, 'w') as f:
            json.dump(list(processed_files), f)
        nx.write_gpickle(G, GRAPH_FULL_GPICKLE)
        logger.info("Completed dependency processing and saved final graph")
    except Exception as e:
        logger.error(f"Error saving final dependency graph: {e}")

    return G


def compute_centrality(G):
    """Compute Katz centrality and PageRank for all Java files."""
    try:
        max_degree = max(d for n, d in G.out_degree()) if G.number_of_nodes() > 0 else 1
        alpha = 0.9 / max_degree
        katz_centrality = nx.katz_centrality(G, alpha=alpha, beta=1.0, max_iter=1000, tol=1e-6)
        logger.info("Computed Katz centrality")
    except nx.PowerIterationFailedConvergence as e:
        logger.error(f"Katz centrality failed to converge: {e}. Using zero centrality.")
        katz_centrality = {node: 0 for node in G.nodes()}

    try:
        pagerank = nx.pagerank(G, alpha=0.85)
        logger.info("Computed PageRank")
    except Exception as e:
        logger.error(f"PageRank computation failed: {e}. Using zero centrality.")
        pagerank = {node: 0 for node in G.nodes()}

    all_files = [node for node in G.nodes() if node.endswith('.java')]
    results = pd.DataFrame({
        'file': all_files,
        'katz_centrality': [katz_centrality.get(f, 0) for f in all_files],
        'pagerank': [pagerank.get(f, 0) for f in all_files]
    })
    results.sort_values('katz_centrality', ascending=False, inplace=True)

    try:
        results.to_csv(OUTPUT_CSV, index=False)
        logger.info(f"Saved centrality results to {OUTPUT_CSV}")
        logger.info("Top 5 high-centrality files:")
        logger.info(f"\n{results.head().to_string()}")
    except IOError as e:
        logger.error(f"Error saving {OUTPUT_CSV}: {e}")


if __name__ == "__main__":
    try:
        g = Github("")
        repo = g.get_repo("")
        local_report_path = ""

        class_to_file = build_class_to_file_mapping(local_report_path)

        # Process commits
        G = process_commits(g, repo, local_report_path)

        # Add dependency edges
        G = add_dependency_edges(G, class_to_file, local_report_path)

        # Compute centrality
        compute_centrality(G)

        logger.info("Analysis completed successfully")
    except Exception as e:
        logger.error(f"Main execution failed: {e}")