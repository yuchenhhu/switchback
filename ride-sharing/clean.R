library(tidyverse)
library(lubridate)
library(zoo)
theme_set(theme_bw())

get_df_aggregated <- function(df, interval, H_t) {
  breaks <- seq(0, H_t, by = interval)
  df$interval <- cut(df$ts, breaks = breaks, include.lowest = T)
  delayed_reward <- data.frame(time = df$ts+df$etd,
                               reward = df$reward)
  delayed_reward$interval <- cut(delayed_reward$time, breaks = breaks, include.lowest = T)
  df_aggregated <- data.frame(time = 1:(length(breaks)-1),
                              avg_trt = round(tapply(df$treatment, df$interval, mean)),
                              #total_reward = tapply(df$reward, df$interval, sum))
                              total_reward = tapply(delayed_reward$reward, delayed_reward$interval, sum))
  df_aggregated[is.na(df_aggregated$total_reward),3] <- 0
  return(df_aggregated)
}

dir <- "switchback/ride_sharing/rideshare-simulator/output/"
setwd("/home/users/yuchenhu")

H_t <- 400000
switch_length <- 2000 # 6000 # 4000

interval <- 400
niter <- 100
treatment_all <- vector(mode='list',length=niter)
control_all <- vector(mode='list',length=niter)
actual_all <- vector(mode='list',length=niter)
for (i in 1:niter) {
  summary <- read_csv(paste0(dir,'summary', i,'.csv'))
  summary$reward <- (summary$price-summary$cost)*summary$accepted
  
  summary_A <- summary %>% 
    filter(world_line == 'A') %>% get_df_aggregated(interval,H_t)
  summary_A$world_line = 'A'
  control_all[[i]] <- summary_A[(switch_length/interval+1):nrow(summary_A),]
  
  summary_B <- summary %>% 
    filter(world_line == 'B') %>% get_df_aggregated(interval,H_t)
  summary_B$world_line = 'B'
  treatment_all[[i]] <- summary_B[(switch_length/interval+1):nrow(summary_B),]
  
  summary_expt <- summary %>% 
    filter(world_line == 'expt') %>% get_df_aggregated(interval,H_t)
  summary_expt$world_line = 'expt'
  actual_all[[i]] <- summary_expt[(switch_length/interval+1):nrow(summary_expt),]
}

# save results
for (i in 1:niter) {
  write.csv(control_all[[i]], paste0(dir,"cleaned_files/control",i,".csv"), row.names = FALSE)
  write.csv(treatment_all[[i]], paste0(dir,"cleaned_files/treatment",i,".csv"), row.names = FALSE)
  write.csv(actual_all[[i]], paste0(dir,"cleaned_files/actual",i,".csv"), row.names = FALSE)
}

#### analysis #### 
# filter
l = switch_length/interval
H = H_t/interval - l
#b = 4
#indices <- unlist(lapply(seq(1, H, by = l), function(start) start + b:(l-1)))

# calculate GATE and FATE
GATE <- NULL
#FATE <- NULL
for (i in 1:niter) {
  GATE <- c(GATE,mean(treatment_all[[i]]$total_reward-control_all[[i]]$total_reward))
  #FATE <- c(FATE,mean(treatment_all[[i]]$total_reward[indices]-control_all[[i]]$total_reward[indices]))
}
mean(GATE)
#mean(FATE)

#### plot ####
summary_expt <- actual_all[[1]][51:90,]
summary_A <- control_all[[1]][51:90,]
summary_B <- treatment_all[[1]][51:90,]
summary_expt$time=summary_expt$time*400
summary_A$time=summary_A$time*400
summary_B$time=summary_B$time*400
trt1_regions <- subset(summary_expt, avg_trt == 1)
trt0_regions <- subset(summary_expt, avg_trt == 0)
df_all <- rbind(summary_A,summary_B,summary_expt)
ggplot(df_all) +
  geom_rect(aes(xmin = time-400, xmax = time, ymin = -Inf, ymax = Inf), data = trt1_regions, fill = "lightskyblue2", alpha = 0.35) +
  geom_rect(aes(xmin = time-400, xmax = time, ymin = -Inf, ymax = Inf), data = trt0_regions, fill = "darkseagreen2", alpha = 0.35) +
  geom_line(aes(time, total_reward, linetype = world_line, color = world_line),size = 1.25) +
  scale_linetype_manual(values = c('expt' = 'solid', 'A' = 'dashed', 'B' = 'dashed'),
                        labels = c('expt' = 'Switchback', 'A' = 'Always treated', 'B' = 'Always in control')) +
  scale_color_manual(values = c('expt' = '#F8766D', 'A' = '#00BA38', 'B' = '#619CFF'),
                     labels = c('expt' = 'Switchback', 'A' = 'Always treated', 'B' = 'Always in control')) +
  scale_x_continuous(limits=c(60*400,100*400)) +
  labs(linetype = "Design", color = "Design",
       y = 'Total Profit', x = 'Time (second)') +
  theme(
    legend.position="top",
    legend.direction="horizontal",
    #legend.position="none",
    panel.grid.minor = element_blank(),
    plot.title = element_text(size = 20),
    axis.text=element_text(size=20),
    legend.title=element_text(size=20),
    legend.text=element_text(size=20),
    axis.title=element_text(size=20,face="bold"),
    panel.grid.major = element_blank()
  )
