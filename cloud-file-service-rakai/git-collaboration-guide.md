# Git Collaboration Guide

## Current Situation

You and your friend are working on different parts:
- **You**: Block storage service and backend architecture
- **Friend**: Client SDK and frontend

**Problem**: Your friend pushed changes while you were working, causing a conflict.

## Quick Solution (Choose One)

### Option 1: Stash and Pull (Recommended)
```bash
# Save your changes temporarily
git stash push -m "My block storage work"

# Get friend's changes
git pull origin main

# Apply your changes back
git stash pop

# If conflicts occur, resolve them manually, then:
git add .
git commit -m "Resolve conflict: merge block storage with frontend"
git push
```

### Option 2: Use the Helper Script
```bash
resolve-git-conflict.bat
```

## Future Prevention Strategies

### Strategy 1: Feature Branches (Recommended)
```bash
# Create a branch for your work
git checkout -b feature/block-storage-enhancement

# Work on your changes
# ... make changes ...

# Commit and push your branch
git add .
git commit -m "Enhance block storage service"
git push -u origin feature/block-storage-enhancement

# Create Pull Request when ready
# Merge through GitHub/GitLab interface
```

### Strategy 2: Communication Protocol
1. **Before starting work**: Check with teammate
2. **Announce your area**: "Working on block storage"
3. **Frequent pulls**: `git pull` before starting each session
4. **Coordinate pushes**: Don't push simultaneously

### Strategy 3: File-based Division
```
Your areas (Block Storage):
- backend/block-storage/
- docker-compose.yml (if needed)
- Testing scripts for block storage

Friend's areas (Frontend/SDK):
- frontend/
- client-sdk/
- Documentation for client usage
```

## Advanced Collaboration Workflow

### Gitflow for Your Project
```bash
# Main branches
main          # Production-ready code
develop       # Integration branch

# Your feature branches
feature/block-storage-service
feature/sync-service-enhancement
feature/metadata-service-fix

# Friend's feature branches  
feature/client-sdk
feature/frontend-ui
feature/authentication
```

### Daily Workflow
```bash
# Start of day
git checkout develop
git pull origin develop
git checkout -b feature/your-work-today

# During work
git add .
git commit -m "Descriptive message"

# End of day
git push -u origin feature/your-work-today

# When feature is complete
# Create Pull Request: feature/your-work → develop
# After review and merge, delete feature branch
```

## Conflict Resolution Steps

### When Conflicts Happen
1. **Don't panic** - conflicts are normal
2. **Communicate** with your friend
3. **Use tools** to resolve systematically

### Manual Resolution
```bash
# 1. See what files have conflicts
git status

# 2. Open conflicted files, look for:
<<<<<<< HEAD
Your changes
=======
Friend's changes  
>>>>>>> branch-name

# 3. Edit to keep what you want:
Combined changes that work

# 4. Mark as resolved
git add conflicted-file.txt

# 5. Complete the merge
git commit -m "Resolve conflict in conflicted-file.txt"
```

## Project Structure for Collaboration

```
cloud-file-service-rakai/
├── backend/                 # Your area
│   ├── block-storage/      # Your main work
│   ├── metadata-service/   # Your changes
│   └── sync-service/       # Your changes
├── frontend/               # Friend's area
├── client-sdk/             # Friend's area
├── docker-compose.yml      # Shared (coordinate)
├── .env                    # Shared (coordinate)
└── docs/                   # Shared
```

## Communication Templates

### Before Starting Work
```
Hey [friend], starting work on:
- Block storage enhancements
- Sync service testing
- Will touch: backend/block-storage/, docker-compose.yml

Your areas safe? Any conflicts I should know about?
```

### Before Pushing
```
Pushing changes to:
- Enhanced block storage service
- New testing scripts
- Updated docker configuration

Can you pull before your next push?
```

### When Conflict Occurs
```
Git conflict detected in:
- docker-compose.yml
- .env file

Can we resolve together? Or should I:
1. Stash my changes
2. Pull yours
3. Reapply mine on top?
```

## Tools to Help

### VS Code Git Integration
- Install "GitLens" extension
- Use built-in merge conflict resolver
- Visual diff comparison

### Command Line Tools
```bash
# See file differences
git diff HEAD~1

# See branch differences  
git log --oneline --graph

# Interactive rebase
git rebase -i HEAD~3
```

## Emergency Recovery

### If You Lose Work
```bash
# Check reflog (Git saves everything)
git reflog

# Restore from reflog
git reset --hard HEAD@{2}

# Or restore from stash
git stash list
git stash apply stash@{0}
```

### If Remote is Broken
```bash
# Create backup
cp -r . ../backup-$(date +%Y%m%d)

# Force reset to working state
git fetch origin
git reset --hard origin/main
```

## Best Practices Summary

1. **Use feature branches** for all work
2. **Pull before push** every time
3. **Communicate actively** about what you're working on
4. **Test after merging** to ensure everything works
5. **Keep commits small** and focused
6. **Write clear commit messages**

## Your Current Action Plan

1. **Immediate**: Run `resolve-git-conflict.bat`
2. **Short-term**: Agree on feature branch workflow with friend
3. **Long-term**: Establish clear areas of ownership
4. **Always**: Test services after resolving conflicts

Remember: The sync service tests you have (`run-sync-test.bat`) will help verify everything still works after resolving conflicts! 🚀
