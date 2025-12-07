from git import Repo
import os

# Path to your local GitHub repo
repo_path = r"C:\Users\Hatim\Documents\Github\SmartAccessControl"
commit_message = "changes"

# Open repo
repo = Repo(repo_path)

if repo.is_dirty(untracked_files=True):
    # Collect changes: modified + untracked
    changed_files = [item.a_path for item in repo.index.diff(None)]  
    changed_files += repo.untracked_files  
    
    for file in changed_files:
        abs_path = os.path.join(repo_path, file)   # type: ignore
        if os.path.exists(abs_path):  
            print(f"Staging and committing: {file}")
            repo.index.add([abs_path])
            repo.index.commit(commit_message)
        else:
            print(f"Skipping missing file: {file}")
else:
    print("No changes to commit.")