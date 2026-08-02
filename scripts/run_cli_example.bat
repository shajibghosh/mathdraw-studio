@echo off
setlocal
call conda activate mathdraw-studio
mathdraw examples\demo_input.png --mode hybrid_vector --output demo_output
