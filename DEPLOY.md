# 배포 가이드 — 로컬 자동수집 + GitHub Pages

이 사이트는 **정적 파일(index.html + data.js)** 이라 GitHub Pages로 무료 호스팅됩니다.
데이터 수집은 **내 맥에서 매일 자동 실행**(launchd)되고, 결과를 GitHub로 push 하면 Pages가 자동 갱신됩니다.

```
[내 맥] 매일 8:30  launchd
   └─ refresh_and_deploy.sh
        ├─ fetch_feeds.py  → data.js/json 갱신 (1년 누적)
        └─ git push        → GitHub → Pages 자동 배포
```

## 이미 세팅된 것 (자동 완료)
- ✅ git 저장소 초기화 + 첫 커밋 (`main` 브랜치)
- ✅ 자동수집 스크립트 `refresh_and_deploy.sh`
- ✅ launchd 에이전트 `com.techclip.refresh` 등록 (매일 오전 8:30)
- ✅ `gh` (GitHub CLI) 설치

## 남은 것 — GitHub 연결 (한 번만)

### 1) GitHub 로그인 (내 터미널에서 직접 1회)
```bash
gh auth login
```
프롬프트 답변: **GitHub.com → HTTPS → Yes(Git 자격증명) → Login with a web browser**
→ 표시되는 8자리 코드를 브라우저에 입력하고 승인하면 끝. (HTTPS 자격증명이 keychain에 저장되어 이후 자동 push가 됩니다.)

### 2) 저장소 생성 + push (로그인 후)
```bash
cd "/Users/suyeon/Downloads/보험사 챗봇/tech_blog_ai_clip"
gh repo create tech-blog-ai-clip --public --source=. --remote=origin --push
```

### 3) GitHub Pages 켜기
```bash
gh api -X POST "repos/{owner}/{repo}/pages" -f "source[branch]=main" -f "source[path]=/"
```
1~2분 뒤 사이트 공개: **https://<GitHub아이디>.github.io/tech-blog-ai-clip/**

> 2)·3) 은 로그인만 해두시면 Claude가 대신 실행해 드립니다.

---

## 자동수집 관리
```bash
# 지금 즉시 한 번 수집·배포 테스트
bash "/Users/suyeon/Downloads/보험사 챗봇/tech_blog_ai_clip/refresh_and_deploy.sh"

# 로그 보기
tail -f "/Users/suyeon/Downloads/보험사 챗봇/tech_blog_ai_clip/refresh.log"

# 실행 시간 바꾸기: com.techclip.refresh.plist 의 Hour/Minute 수정 후
launchctl unload ~/Library/LaunchAgents/com.techclip.refresh.plist
cp "/Users/suyeon/Downloads/보험사 챗봇/tech_blog_ai_clip/com.techclip.refresh.plist" ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.techclip.refresh.plist

# 자동수집 끄기
launchctl unload ~/Library/LaunchAgents/com.techclip.refresh.plist
```
> 맥이 꺼져 있거나 자는 동안 8:30이 지나면, 깨어난 직후 한 번 실행됩니다.
> (맥을 켜두지 않는 날은 그날 수집이 건너뛰어집니다 — 새 글은 다음 실행 때 누적됩니다.)

## 인증 없이 가장 간단히 (대안)
GitHub 없이 그냥 공개만 하려면 [app.netlify.com/drop](https://app.netlify.com/drop) 에
`tech_blog_ai_clip` 폴더를 끌어다 놓으면 즉시 공개 URL이 나옵니다.
단, 이 경우 자동 갱신은 안 되고 폴더를 다시 올려야 합니다.
