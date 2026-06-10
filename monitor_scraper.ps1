while ($true) {
  try {
    if (Test-Path "comun/datos/brutos/ram/detalle_ram.json") {
      $content = Get-Content "comun/datos/brutos/ram/detalle_ram.json" -Raw -ErrorAction Stop
      $json = $content | ConvertFrom-Json
      $m = $json.metadata
      $processed = [int]$m.total_procesados_ok
      $total = [int]$m.total_productos
      $state = $m.estado
      $last = $m.ultimo_id_procesado
      $sizeMB = [math]::Round((Get-Item "comun/datos/brutos/ram/detalle_ram.json").Length / 1MB, 1)
      $time = Get-Date -Format "HH:mm:ss"
      Write-Output "[$time] $processed / $total | Estado: $state | Ultimo: $last | Tamano: $sizeMB MB"
      if ($state -eq "completado" -and $processed -ge $total) {
        Write-Output "=== SCRAPER TERMINADO DEL TODO: $processed / $total productos con resenas ==="
        Write-Output "=== LISTO PARA COMMIT ==="
        break
      }
    } else {
      Write-Output "JSON no existe todavia..."
    }
  } catch {
    Write-Output "Error al leer: $($_.Exception.Message)"
  }
  Start-Sleep -Seconds 60
}
