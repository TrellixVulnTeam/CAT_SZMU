#!/bin/bash

if [ ! -d "OutputBert" ]; then
  mkdir OutputBert
fi

for id in 0 1 2 3 4
do
    CUDA_VISIBLE_DEVICES=0 python run_cat.py \
	--experiment mixceleba \
	--approach mlp_cat_ncl \
	--note random$id,ntasks30 \
	--dis_ntasks 20 \
	--classptask 5 \
	--idrandom $id \
	--lr 0.025 \
	--lr_patience 10 \
	--n_head 5 \
	--data_size small \
	--similarity_detection auto \
	--loss_type multi-loss-joint-Tsim
done