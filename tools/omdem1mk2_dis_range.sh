#!/bin/sh
# Disassemble a CPU address range of the stock E-M1 II main (run inside the em1emu container).
# usage: sh tools/omdem1mk2_dis_range.sh START END
B=0x60021020
S=$(($1)); E=$(($2))
/home/hertzel/ep7fw-toolchains/mn10300/bin/mn10300-elf-objdump -D -b binary -m mn10300 \
  --adjust-vma=$((B)) --start-address=$S --stop-address=$E \
  /work/em1mk2/extracted/00_0100_40560020.decoded.bin | tail -n +8
