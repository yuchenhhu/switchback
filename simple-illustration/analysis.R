library(ggplot2) 
library(patchwork)
library(egg)
library(dplyr)
theme_set(theme_bw())

#### sim_b_10_80_l_30 #### 
H_all = 2^(2:8)*100
b_all = seq(10,80,10)
l_all = b_all+30

plot_df_b <- data.frame(
  mse = numeric(),
  type = factor(),
  H = numeric(),
  l = numeric(),
  b = numeric(),
  stringsAsFactors = FALSE
)
for (H in H_all) {
  res <- read.csv(paste0("/home/users/yuchenhu/switchback/sim_mdp/sim_new/sim_b_10_80_l_30/result_T", H, ".csv"),header = F)
  plot_df_b <- rbind(plot_df_b,data.frame(mse=c(as.numeric(res[4,]),as.numeric(res[5,])),
                                          type=factor(rep(c("FATE","BC"),each=length(b_all)),levels=c("FATE","BC")),
                                          H=rep(H,2*length(b_all)),
                                          l=rep(l_all,2),
                                          b=rep(b_all,2)))
}

H_all_grid <- 2^seq(2,8,0.2)*100
plot_df_rate_log <- data.frame(H=rep(H_all_grid,each=length(-3:8)),
                           rate=as.numeric(outer(2^(-3:8)*50,(H_all_grid)^(-1)*log(H_all_grid))),
                           group=rep(-3:8,length(H_all_grid)))

g1 <- ggplot(plot_df_b[plot_df_b$type=="FATE",]) +
  #geom_line(aes(H,mse,group=interaction(l,b),color=l,linetype=b)) +
  geom_line(aes(H,mse,group=interaction(l,b),color=b)) +
  geom_line(aes(H,rate,group=group),plot_df_rate_log,linetype="dashed") +
  coord_cartesian(ylim=c(0.005,256)) +
  scale_x_continuous(trans='log2',breaks=H_all)+#,limits=c(min(c(plot_df$H,plot_df_b$H)), max(c(plot_df$H,plot_df_b$H))))+
  scale_y_continuous(trans='log2')+#,limits=c(0.005,16))+#,limits=c(min(c(plot_df$mse,plot_df_b$mse)), max(c(plot_df$mse,plot_df_b$mse))))+
  #scale_x_discrete(expand=c(0.05,0.02)) +
  scale_colour_gradientn(colours = c("orange","darkred"))+
  annotate("text", x = 800, y = 0.3, label = 'log(T)~T^{-1}', parse = TRUE, size = 6) +
  ylab('Mean Squared Error') +
  xlab('T') +
  ggtitle(label = "Difference-in-means with burn-ins")+
  theme(
    #legend.position=c(.4, .7),
    legend.direction="horizontal",
    legend.position="none",
    panel.grid.minor = element_blank(),
    plot.title = element_text(size = 20),
    axis.text=element_text(size=20),
    axis.title=element_text(size=20,face="bold"),
    panel.grid.major = element_blank()
  )

g2 <- ggplot(plot_df_b[plot_df_b$type=="BC",]) +
  #geom_line(aes(H,mse,group=interaction(l,b),color=l,linetype=b)) +
  geom_line(aes(H,mse,group=interaction(l,b),color=b)) +
  geom_line(aes(H,rate,group=group),plot_df_rate_log,linetype="dashed") +
  coord_cartesian(ylim=c(0.005,256)) +
  scale_x_continuous(trans='log2',breaks=H_all)+#,limits=c(min(c(plot_df$H,plot_df_b$H)), max(c(plot_df$H,plot_df_b$H))))+
  scale_y_continuous(trans='log2')+#,limits=c(0.005,16))+#,limits=c(min(c(plot_df$mse,plot_df_b$mse)), max(c(plot_df$mse,plot_df_b$mse))))+
  #scale_x_discrete(expand=c(0.05,0.02)) +
  scale_colour_gradientn(colours = c("orange","darkred"))+
  annotate("text", x = 800, y = 0.3, label = 'log(T)~T^{-1}', parse = TRUE, size = 6) +
  ylab('Mean Squared Error') +
  xlab('T') +
  ggtitle(label = "Bias-corrected")+
  theme(
    #legend.position=c(.4, .7),
    legend.direction="horizontal",
    legend.position="none",
    plot.title = element_text(size = 20),
    panel.grid.minor = element_blank(),
    axis.text=element_text(size=20),
    axis.title=element_text(size=20,face="bold"),
    panel.grid.major = element_blank()
  )

# find which l is better for each H
best_l_FATE <- plot_df_b %>%
  filter(type == 'FATE') %>%
  group_by(H) %>%
  filter(mse == min(mse)) %>%
  ungroup()

best_l_BC <- plot_df_b %>%
  filter(type == 'BC') %>%
  group_by(H) %>%
  filter(mse == min(mse)) %>%
  ungroup()


#### sim_l_60_480 ####
H_all <- 2^(2:8)*100
l_all <- seq(60,480,60)

plot_df <- data.frame(
  mse = numeric(),
  H = numeric(),
  l = numeric(),
  stringsAsFactors = FALSE
)
for (H in H_all) {
  res <- read.csv(paste0("/home/users/yuchenhu/switchback/sim_mdp/sim_new/sim_l_60_480/result_T", H, ".csv"),header = F)
  plot_df <- rbind(plot_df,data.frame(mse=as.numeric(res[2,]),
                                      H=rep(H,length(l_all)),
                                      l=l_all))
}

plot_df_rate <- data.frame(H=rep(H_all_grid,each=length(-3:8)),
                           rate=as.numeric(outer(2^(-3:8)*50,(H_all_grid)^(-2/3))),
                           group=rep(-3:8,length(H_all_grid)))

g3 <- ggplot(plot_df) +
  geom_line(aes(H,mse,group=l,color=l)) +
  geom_line(aes(H,rate,group=group),plot_df_rate,linetype="dashed") +
  coord_cartesian(ylim=c(0.005,256)) +
  scale_x_continuous(trans='log2',breaks=H_all)+#,limits=c(min(c(plot_df$H,plot_df_b$H)), max(c(plot_df$H,plot_df_b$H))))+
  scale_y_continuous(trans='log2')+#,limits=c(min(c(plot_df$mse,plot_df_b$mse)), max(c(plot_df$mse,plot_df_b$mse))))+
  #scale_x_discrete(expand=c(0.05,0.02)) +
  scale_colour_gradientn(colours = c("orange","darkred"))+
  annotate("text", x = 800, y = 0.3, label = 'T^{-2/3}', parse = TRUE, size = 6) +
  ylab('Mean Squared Error') +
  xlab('T') +
  ggtitle(label = "Difference-in-means")+
  theme(
    #legend.position=c(.4, .7),
    legend.direction="horizontal",
    legend.position="none",
    panel.grid.minor = element_blank(),
    plot.title = element_text(size = 20),
    axis.text=element_text(size=20),
    axis.title=element_text(size=20,face="bold"),
    panel.grid.major = element_blank()
  )

#### plot ####

ggarrange(g3, 
          g1 + 
            theme(axis.text.y = element_blank(),
                  axis.ticks.y = element_blank(),
                  axis.title.y = element_blank() ), 
          g2 + 
            theme(axis.text.y = element_blank(),
                  axis.ticks.y = element_blank(),
                  axis.title.y = element_blank() ),
          nrow = 1)

# find which l is better for each H
best_l_DM <- plot_df %>%
  group_by(H) %>%
  filter(mse == min(mse)) %>%
  ungroup()

best_l_df <- data.frame(l=c(best_l_DM$l,best_l_FATE$l,best_l_BC$l),
                        H=rep(best_l_DM$H,3),
                        type=rep(c('DM','DMB','BC'),each=nrow(best_l_DM)))

ggplot(best_l_df) +
  geom_line(aes(H,l,color=type))
