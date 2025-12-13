library(ggplot2)
theme_set(theme_bw())

# read data
dir <- "switchback/ride_sharing/rideshare-simulator/output/"
setwd("/home/users/yuchenhu")
# please note that treatment in the paper is marked as control here

# find average ride length + histogram for Figure 5 (left panel)
i=1
summary <- read.csv(paste0(dir,'summary', i,'.csv'))
mean(summary$etd[summary$world_line=="A"])
hist(summary$etd[(summary$world_line=="A")&(summary$etd<=10000)],breaks=seq(0,10000,1000))

ggplot(summary[summary$world_line == "A" & summary$etd <= 10000, ], 
       aes(x = etd)) +
  geom_histogram(breaks = seq(0, 10000, 100),
                 aes(y = after_stat(count / sum(count)))) +
  labs(x = "Expected Duration",y = "Proportion") +
  scale_x_continuous(breaks = seq(0, 10000, 2000))+
  theme(
    panel.grid.minor = element_blank(),
    plot.title = element_text(size=18,face="bold"),
    axis.text=element_text(size=24),
    axis.title=element_text(size=24),
    strip.text = element_text(size = 24)
  ) + theme(legend.position="none")


# reproducing Figure 5 (right panel)
res_table <- read.csv("switchback/ride_sharing/rideshare-simulator/lepski_plot.csv", header=F)
res_table <- -res_table
res_df <- data.frame(value = c(c(res_table$V1[1],res_table$V2),
                               c(res_table$V1[1],res_table$V3),
                               c(res_table$V4[1],res_table$V5),
                               c(res_table$V4[1],res_table$V6)),
                     b = rep((0:nrow(res_table))*4,4),
                     type = rep(c('estimator','standard error'),each=2*(nrow(res_table)+1)),
                     Estimator = rep(rep(c('DM','BC'),each=nrow(res_table)+1),2))

ggplot(res_df[res_df$type=='estimator',]) +
  geom_line(aes(b,value,color=Estimator),linewidth=1.5) +
  labs(x = "Burn-In Period Length",y = "") +
  scale_x_continuous(breaks = seq(0, 32, 4))+
  scale_color_manual(values = c('DM' = '#F8766D', 'BC' = '#00BA38')) +#, 'B' = '#619CFF'))
  theme(
    panel.grid.minor = element_blank(),
    plot.title = element_text(size=18,face="bold"),
    axis.text=element_text(size=24),
    axis.title=element_text(size=24),
    legend.text=element_text(size=24),
    legend.title=element_text(size=24),
    strip.text = element_text(size = 24)
  ) + theme(legend.position="top")


# compute HT estimator for Table S4 (second part)
dir <- "switchback/ride_sharing/rideshare-simulator/output/"
setwd("/home/users/yuchenhu")

niter <- 100
H <- 990
l <- 10
tau_hat <- c()

for (i in 1:niter) {
  actual <- read.csv(paste0(dir,"cleaned_files/actual",i,".csv"))
  actual$roll_sum <- zoo::rollsum(actual$avg_trt, k=l+1, align="right", fill=NA)
  actual$all1 <- as.integer(actual$roll_sum == (l+1))
  actual$all0 <- as.integer(actual$roll_sum == 0)
  actual <- actual[(l+1):nrow(actual),]
  tau_hat <- c(tau_hat,mean(actual$total_reward[actual$all1==1]) - mean(actual$total_reward[actual$all0==1]))
}

tau = -13.90982
abs(mean(tau_hat-tau))
sqrt(var(tau_hat))
mean((tau_hat-tau)^2)

