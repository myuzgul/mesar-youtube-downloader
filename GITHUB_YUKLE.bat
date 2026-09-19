@echo off
chcp 65001 >nul
echo =================================================================
echo   MESAR YOUTUBE DOWNLOADER - GITHUB YÜKLEME ARACI
echo =================================================================
echo.
echo Lütfen GitHub'da oluşturduğunuz yeni reponun HTTPS linkini yapıştırın:
echo (Örnek: https://github.com/kullaniciadi/mesar-youtube-downloader.git)
echo.
set /p REPO_URL="GitHub Repo Linki: "

if "%REPO_URL%"=="" (
    echo Hata: Link girmediniz.
    pause
    exit /b
)

git remote remove origin 2>nul
git remote add origin %REPO_URL%
git branch -M main
echo.
echo GitHub'a yükleniyor, lütfen bekleyin...
git push -u origin main

echo.
echo =================================================================
echo   YÜKLEME BAŞARIYLA TAMAMLANDI!
echo =================================================================
echo.
echo Şimdi Render.com'a gidip bu depoyu seçerek 'Deploy' diyebilirsiniz.
echo.
pause
