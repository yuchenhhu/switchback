library(ggplot2)
library(tidyverse)
library(lubridate)
library(zoo)
library(gridExtra)
theme_set(theme_bw())

dir <- "/home/users/yuchenhu/switchback/sim_mdp_mixing/"
setwd(dir)


var_easy_mat <- read.csv(paste0(dir,'sim_toy_var_easy.csv'),header=F)
var_hard_mat <- read.csv(paste0(dir,'sim_toy_var_hard.csv'),header=F)

ratio_df <- data.frame(ratio = c(var_easy_mat$V4/var(var_easy_mat$V1),
                                 var_easy_mat$V5/var(var_easy_mat$V2),
                                 var_easy_mat$V6/var(var_easy_mat$V3),
                                 var_hard_mat$V4/var(var_hard_mat$V1),
                                 var_hard_mat$V5/var(var_hard_mat$V2),
                                 var_hard_mat$V6/var(var_hard_mat$V3)),
                       estimator = rep(rep(c('DM','DMB','BC'),each=nrow(var_easy_mat)),2),
                       type = rep(c('Mixing','Original'),each=3*nrow(var_easy_mat)))

estimator_levels <- c('DM', 'DMB', 'BC')
ratio_df$estimator <- factor(ratio_df$estimator, levels = estimator_levels)
type_levels <- c('Original', 'Mixing')
ratio_df$type <- factor(ratio_df$type, levels = type_levels)

ggplot(ratio_df) +
  geom_boxplot(aes(x=estimator, y=ratio),
               notch=TRUE,
               notchwidth = 0.8) + 
  stat_boxplot(aes(x=estimator, y=ratio), geom = 'errorbar') +
  geom_hline(aes(yintercept=1),linetype='dashed') +
  ylab('Estimated Variance Ratio')+
  xlab('Estimator')+
  facet_wrap(~type)+
  theme(
    legend.position="top",
    legend.direction="horizontal",
    #legend.position="none",
    panel.grid.minor = element_blank(),
    plot.title = element_text(size = 20),
    axis.text=element_text(size=20),
    legend.title=element_text(size=20),
    legend.text=element_text(size=20),
    strip.text = element_text(size = 20),
    axis.title=element_text(size=20,face="bold"),
    panel.grid.major = element_blank()
  )
