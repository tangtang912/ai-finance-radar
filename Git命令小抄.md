# Git 命令小抄（写完代码 → 传 GitHub）

```bash
cd "/Users/ty/Desktop/AI财报异动雷达项目"   # 1. 进门：进到项目文件夹（不算 git 命令）
git add .                                   # 2. 打包：把所有改动放进"待发清单"
git commit -m "完成5号异动雷达"              # 3. 盖章：写清楚这次改了什么
git push                                    # 4. 发出：上传到 GitHub（不用 -f 了）
```

其他常用：

```bash
git status          # 查看：哪些文件改过了、哪些还没 add（心里没底就先看它）
git log --oneline   # 查看：发过哪些 commit
```

## 两条规则

1. **push 前先喊 Claude 看一眼**（约定）
2. `data/`、`.env`、密钥永不进仓库（.gitignore 已经挡好了，`git add .` 也不会误带）
