# 금융통계학 웹북

금융통계학의 주요 개념을 수식, 그림, 코드 예제, 실습, 개념 설명 링크와 함께 제공하는 웹북.

GitHub 저장소: [ksublee/finstat](https://github.com/ksublee/finstat)

공개 웹북: [ksublee.github.io/finstat](https://ksublee.github.io/finstat/)


## 자동 렌더링과 배포

`.github/workflows/quarto-pages.yml`은 PR에서 웹북 전체를 새로 렌더링하고,
`main`에 병합한 뒤에는 같은 결과물을 GitHub Pages에 배포합니다.
PR은 배포하지 않습니다. 실패한 렌더링 결과도 배포하지 않습니다.
Actions의 `github-pages` artifact에서 렌더링 결과를 내려받아 확인할 수 있습니다.

### 최초 전환 (저장소 관리자)

1. 이 PR의 `Render and check book` 검사를 확인합니다.
2. [Settings → Pages](https://github.com/ksublee/finstat/settings/pages)에서
   **Build and deployment → Source → GitHub Actions**를 선택합니다.
   기존 `main /docs` 배포와 새 워크플로가 동시에 배포하지 않도록 전환합니다.
3. PR을 병합합니다. 이후에는 원본 `.qmd`와 필요한 리소스만 수정하면 됩니다.
   이미 추적 중인 `docs/`는 이전 배포의 기록이며 새 워크플로는 매번 이를 지우고
   다시 생성한 artifact만 배포합니다. 생성 결과를 새로 커밋할 필요가 없습니다.

이 PR 자체는 Pages 설정을 바꾸거나 사이트를 배포하지 않습니다.
수동 재실행은 Actions → Render and publish Quarto book → Run workflow에서
`main`을 선택합니다. 다른 브랜치의 수동 실행은 검사만 합니다.

### 로컬 확인

Quarto 1.9.38, R 4.5.2와 R 패키지 `knitr`, `rmarkdown`을 사용합니다.

```sh
Rscript -e 'install.packages(c("knitr", "rmarkdown"), repos="https://cloud.r-project.org")'
quarto render --to html --output-dir _preview
python3 scripts/check-render.py _preview
```

현재 `{r}` 청크 2개는 모두 `eval: false`입니다. `rugarch` 예제는 일반 코드 블록이며,
Backtesting 실습은 저장소에 포함된 webR 확장으로 브라우저에서 실행합니다.
따라서 CI에 `rugarch`나 외부 데이터 다운로드는 필요하지 않습니다.
새 실행 청크에 패키지/데이터 의존성이 생기면 워크플로의 패키지 목록과 리소스를
함께 추가해야 합니다. R 패키지는 호환되는 최신 버전을 설치하며 lockfile은 없습니다.

검사는 전체 목차 페이지, 원본 assets의 복사, 검색 인덱스, 수식과 webR 마크업을
확인합니다. 실제 브라우저의 webR 실행이나 수식 렌더링까지 확인하는 검사는 아닙니다.
