Write-Host "========================================="
Write-Host " SRFM Quantum Phase14 Full Pipeline"
Write-Host "========================================="

python .\scripts\01_import_phase13_memory_landscape.py

python .\scripts\02_build_basin_coordinate_space.py

python .\scripts\03_analyze_basin_entropy.py

python .\scripts\04_build_basin_transition_matrix.py

python .\scripts\05_analyze_basin_boundary_thickness.py

python .\scripts\06_make_phase14_figures.py

python .\scripts\07_build_phase14_summary_tables.py

Write-Host ""
Write-Host "========================================="
Write-Host " Generating PDF"
Write-Host "========================================="

cd .\paper

pandoc phase14_interim_summary.md `
  -o phase14_interim_summary.pdf `
  --pdf-engine=xelatex `
  --toc `
  --number-sections `
  -V mainfont="Times New Roman" `
  -V geometry:margin=1in `
  -V fontsize=11pt

Write-Host ""
Write-Host "========================================="
Write-Host " Phase14 pipeline complete."
Write-Host "========================================="