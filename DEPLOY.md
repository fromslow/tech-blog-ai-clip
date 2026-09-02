# 배포 가이드 — 로컬 자동수집 + GitHub Pages (fine-grained PAT)

이 사이트는 **정적 파일(index.html + data.js)** 이라 GitHub Pages로 무료 호스팅됩니다.
데이터 수집은 **내 맥에서 매일 자동 실행**(launchd)되고, 결과를 GitHub로 push 하면 Pages가 자동 갱신됩니다.

```
[내 맥] 매일 8:30  launchd
   └─ refresh_and_deploy.sh
        ├─ fetch_feeds.py  → data.js/json 갱신 (1년 누적)
        └─ git push        → GitHub → Pages 자동 배포
```

프로젝트 위치: `/Users/suyeon/AI Clipping`

## 이미 세팅된 것 (자동 완료)
- ✅ git 저장소 + 커밋 (`main` 브랜치)
- ✅ 자동수집 스크립트 `refresh_and_deploy.sh`
- ✅ launchd 에이전트 `com.techclip.refresh` (매일 오전 8:30)
- ✅ git 자격증명 helper = osxkeychain (한 번 인증하면 이후 자동 push)

## 남은 것 — GitHub 연결 (한 번만)

### 1) GitHub에 빈 저장소 만들기 (웹)
[github.com/new](https://github.com/new) →
- Repository name: **tech-blog-ai-clip**
- **Public** 선택
- README/gitignore/license 추가하지 **않음**
- **Create repository**

### 2) fine-grained PAT 발급 (웹) — 조직 접근 원천 차단
[github.com/settings/tokens?type=beta](https://github.com/settings/tokens?type=beta) → **Generate new token**
- Token name: `ai-clipping-deploy`
- **Resource owner: 본인 계정(fromslow)** ← ⚠️ BOAZ-bigdata 아님! 이게 조직 격리의 핵심
- Expiration: 원하는 기간 (예: 90 days)
- **Repository access → Only select repositories → `tech-blog-ai-clip`**
- **Permissions → Repository permissions**:
  - **Contents: Read and write**
  - **Pages: Read and write**
  - (Metadata: Read-only 는 자동 포함)
- **Generate token** → 토큰 문자열 복사 (한 번만 보임)

> 이렇게 하면 이 토큰은 오직 `tech-blog-ai-clip` 저장소에만 접근 가능하고, BOAZ-bigdata를 포함한 다른 어떤 저장소·조직에도 접근할 수 없습니다.

### 3) 원격 연결 + 첫 push (내 터미널에서)
```bash
cd "/Users/suyeon/AI Clipping"
git remote add origin https://github.com/fromslow/tech-blog-ai-clip.git
git push -u origin main
```
push 하면 인증을 물어봅니다:
- **Username:** `fromslow`
- **Password:** 방금 복사한 **PAT 붙여넣기** (GitHub 비밀번호 아님)

→ keychain에 저장되어 이후 **매일 자동 push가 인증 없이** 됩니다.

### 4) GitHub Pages 켜기 (웹)
저장소 → **Settings → Pages** → Source: **Deploy from a branch** →
Branch: **main** / **/(root)** → **Save**

1~2분 뒤 공개: **https://fromslow.github.io/tech-blog-ai-clip/**

---

## 자동수집 관리
```bash
# 지금 즉시 한 번 수집·배포
bash "/Users/suyeon/AI Clipping/refresh_and_deploy.sh"

# 로그 보기
tail -f "/Users/suyeon/AI Clipping/refresh.log"

# 실행 시간 변경: com.techclip.refresh.plist 의 Hour/Minute 수정 후
launchctl unload ~/Library/LaunchAgents/com.techclip.refresh.plist
cp "/Users/suyeon/AI Clipping/com.techclip.refresh.plist" ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.techclip.refresh.plist

# 자동수집 끄기
launchctl unload ~/Library/LaunchAgents/com.techclip.refresh.plist
```
> 맥이 자는 동안 8:30이 지나면 깨어난 직후 1회 실행됩니다.
> 맥이 꺼져 있던 날은 그날 수집이 건너뛰어지고, 새 글은 다음 실행 때 누적됩니다.

## 토큰 만료 시
PAT 만료 후 push가 실패하면, 2)번으로 새 토큰을 발급하고 다음으로 keychain을 갱신:
```bash
git credential-osxkeychain erase <<EOF
protocol=https
host=github.com
EOF
```
그다음 `git push` 하면 새 토큰을 다시 물어봅니다.
