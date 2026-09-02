#!/bin/bash
# 테크 블로그 AI 클리핑 - 매일 자동 수집 & 배포
# launchd(com.techclip.refresh) 가 하루 한 번 실행합니다.
#   1) fetch_feeds.py 로 새 글 수집 + 1년 누적
#   2) data.js / data.json 변경분을 커밋
#   3) origin(main) 으로 push  ->  GitHub Pages 자동 갱신
set -uo pipefail

DIR="/Users/suyeon/AI Clipping"
PY="/Users/suyeon/AI Clipping/.venv/bin/python"
LOG="$DIR/refresh.log"

cd "$DIR" || exit 1
echo "===== $(date '+%Y-%m-%d %H:%M:%S') 수집 시작 =====" >> "$LOG"

# 1) 수집 + 누적
"$PY" fetch_feeds.py >> "$LOG" 2>&1

# 2~3) git 저장소면 변경분 커밋 & push
if git rev-parse --git-dir >/dev/null 2>&1; then
  if ! git diff --quiet -- data.js data.json 2>/dev/null; then
    git add data.js data.json
    git commit -m "chore: refresh AI clips ($(date '+%Y-%m-%d'))" >> "$LOG" 2>&1
    if git remote get-url origin >/dev/null 2>&1; then
      if git push origin HEAD >> "$LOG" 2>&1; then
        echo "  -> push 완료 (GitHub Pages 갱신됨)" >> "$LOG"
      else
        echo "  -> push 실패: 원격/인증(PAT) 확인 필요" >> "$LOG"
      fi
    else
      echo "  -> origin 원격 미설정 (DEPLOY.md 참고). 로컬 커밋만 됨." >> "$LOG"
    fi
  else
    echo "  -> 변경 없음" >> "$LOG"
  fi
fi
echo "" >> "$LOG"
