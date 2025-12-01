# Script para normalizar los finales de línea y prevenir corrupciones
# Este script soluciona el problema de duplicación de caracteres al editar archivos

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Normalizando Finales de Línea" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Paso 1: Configurar Git para usar LF en todos lados
Write-Host "1. Configurando Git..." -ForegroundColor Yellow
git config core.autocrlf false
git config core.eol lf
Write-Host "   ✓ Git configurado para usar LF" -ForegroundColor Green
Write-Host ""

# Paso 2: Crear .gitattributes si no existe
Write-Host "2. Creando .gitattributes..." -ForegroundColor Yellow
$gitattributes = @"
# Normalizar finales de línea
* text=auto eol=lf

# Archivos específicos
*.py text eol=lf
*.js text eol=lf
*.html text eol=lf
*.css text eol=lf
*.json text eol=lf
*.md text eol=lf
*.txt text eol=lf
*.sh text eol=lf
*.yml text eol=lf
*.yaml text eol=lf

# Archivos binarios
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.db binary
*.sqlite binary
*.sqlite3 binary
"@

Set-Content -Path ".gitattributes" -Value $gitattributes -Encoding UTF8
Write-Host "   ✓ .gitattributes creado" -ForegroundColor Green
Write-Host ""

# Paso 3: Normalizar archivos existentes
Write-Host "3. Normalizando archivos existentes..." -ForegroundColor Yellow
Write-Host "   (Esto puede tomar un momento)" -ForegroundColor Gray

# Guardar cambios actuales
git add -A
$hasChanges = git status --porcelain
if ($hasChanges) {
    Write-Host "   ⚠ Hay cambios sin commitear. Creando commit temporal..." -ForegroundColor Yellow
    git commit -m "temp: antes de normalizar line endings"
}

# Normalizar
git add --renormalize .
git status --short

Write-Host "   ✓ Archivos normalizados" -ForegroundColor Green
Write-Host ""

# Paso 4: Crear commit con los cambios
Write-Host "4. Guardando cambios..." -ForegroundColor Yellow
$normalized = git status --porcelain
if ($normalized) {
    git commit -m "fix: normalizar finales de línea a LF"
    Write-Host "   ✓ Cambios guardados en Git" -ForegroundColor Green
} else {
    Write-Host "   ℹ No hay cambios que guardar" -ForegroundColor Gray
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ Normalización Completada" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Configuración actual de Git:" -ForegroundColor Cyan
Write-Host "  core.autocrlf: $(git config core.autocrlf)" -ForegroundColor White
Write-Host "  core.eol: $(git config core.eol)" -ForegroundColor White
Write-Host ""
Write-Host "✨ Ahora puedes editar archivos sin problemas de corrupción" -ForegroundColor Green
Write-Host ""
