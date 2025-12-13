using Random, Distributions, LinearAlgebra, Statistics, JLD, DelimitedFiles

H_all = 0:20
M_all = 1:3

function sim_environment(T,pm=0.5)
    m = fill(99, T)
    m[1] = sample(M_all,1)[1]
    for i = 2:T
        mbin = rand(Bernoulli(pm), 1)[1]
        if mbin==1
            m[i] = sample(M_all,1)[1]
        else
            m[i] = m[i-1]
        end
    end
    return m
end

function mu_func(h,w)
    return h+0.5*w*h
end 

function get_design(T,l,pw)
    k = ceil(Int,T/l)
    assignment = rand(Bernoulli(pw), k)
    switchback = repeat(assignment,inner=l)
    return switchback[1:T]
end 

function get_htaut(w,y,T)
    one = fill(1, T)
    pw_hat = sum(w)/length(w)
    if pw_hat==0
        taut = - (one.-w).*y./(1-pw_hat)
    elseif pw_hat==1
        taut = w.*y./pw_hat
    else
        taut = w.*y./pw_hat - (one.-w).*y./(1-pw_hat)
    end
    return taut
end 

function get_htaut_weighted(w,y,T,l)
    weight_w_11 = w[(l+1):T].*w[1:(T-l)]
    weight_w_00 = (1 .- w[(l+1):T]).*(1 .- w[1:(T-l)])
    p11_hat = sum(weight_w_11)/length(weight_w_11)
    p00_hat = sum(weight_w_00)/length(weight_w_00)
    if (p11_hat==0)&(p00_hat==0)
        taut = fill(0, T-l)
    elseif p11_hat==0
        taut = - weight_w_00.*y[(l+1):T]./p00_hat
    elseif p00_hat==0
        taut = weight_w_11.*y[(l+1):T]./p11_hat
    else
        taut = weight_w_11.*y[(l+1):T]./p11_hat - weight_w_00.*y[(l+1):T]./p00_hat
    end
    return taut
end 

function get_burnin(b,l,T)
    burnin = zeros(0)
    k = ceil(Int,T/l)
    for i in 1:(k-1)
        append!(burnin, (l*(i-1)+1):(l*(i-1)+b))
    end
    append!(burnin, (l*(k-1)+1):min(l*(k-1)+b,T))
    return Int.(burnin)
end

function sim_switchback(T,m,w,mixing,ph=0.7,pw=0.5)
    
    # create matrices for storage
    h = fill(99, T)
    mu = fill(99.99, T)
    
    # get initial state
    h[1] = sample(H_all,1)[1]
    mu[1] = mu_func(h[1],w[1])
    
    # transition
    for i = 2:T
        hprob = ph*w[i] + (1-ph)*(1-w[i])
        hbin = rand(Bernoulli(hprob), 1)[1]
        if hbin==1
            h[i] = min(h[i-1]+m[i], 20)
        else
            if mixing
                h[i] = H_all[1]
            else
                h[i] = max(h[i-1]-m[i], 0)
            end
        end
        mu[i] = mu_func(h[i],w[i])
    end

    return mu
end

function sim_switchback_all(T,b,l,m,mixing,sigma=3,ph=0.7,pm=0.5,pw=0.5,burn=50)

    # simulate truth once
    mu1 = sim_switchback(T, m, fill(1, T), false)
    mu0 = sim_switchback(T, m, fill(0, T), false)
    tau = mean(mu1) - mean(mu0)

    # decide burn-in
    burnin = get_burnin(b,l,T)
    tau_FATE = mean(mu1[setdiff(1:T, burnin)]) - mean(mu0[setdiff(1:T, burnin)])
    
    # switchback assignment
    w = get_design(T,l,pw)
    
    # outcome
    mu = sim_switchback(T,m,w,mixing,ph,pw)
    y = mu .+ rand(Normal(0,sigma), T)
    
    # estimator 1 - difference-in-means
    htau_dm_t = get_htaut(w,y,T)
    htau_dm = mean(htau_dm_t)

    # estimator 2 - difference-in-means with burn-in
    htau_dmb = mean(htau_dm_t[setdiff(1:T, burnin)])

    # estimator 4 - bias corrected
    htaut_IPW = get_htaut_weighted(w,y,T,l)
    htaut_IPW_appended = vcat(fill(0, l), htaut_IPW)
    htau_bc = htau_dmb*(l-b)/l + mean(htaut_IPW_appended[setdiff(burnin,1:l)])*b/l
    
    return [tau,tau_FATE,htau_dm,htau_dmb,htau_bc]
end

# simulation
seed_num = 100
Random.seed!(seed_num)

T_all = 2 .^ collect(2:8) .* 100
b_all = collect(10:10:80)
l_all = b_all .+ 30
B = 5000

# simulate environment 
task_id = parse(Int, ENV["SLURM_ARRAY_TASK_ID"])
T = T_all[task_id]
m = sim_environment(T)

tau = zeros(0)
tau_FATE = zeros(0)
htau_dm_mse = zeros(0)
htau_dmb_mse = zeros(0)
htau_bc_mse = zeros(0)

for b_l in 1:length(l_all)
    res_b1 = zeros(0)
    res_b2 = zeros(0)
    res_b3 = zeros(0)
    res_b4 = zeros(0)
    res_b5 = zeros(0)
    for b in 1:B
        result = sim_switchback_all(T,b_all[b_l],l_all[b_l],m,false)
        append!(res_b1,result[1])
        append!(res_b2,result[2])
        append!(res_b3,result[3])
        append!(res_b4,result[4])
        append!(res_b5,result[5])
    end
    append!(tau,mean(res_b1))
    append!(tau_FATE,mean(res_b2))
    append!(htau_dm_mse,mean((res_b3.-mean(res_b1)).^2))
    append!(htau_dmb_mse,mean((res_b4.-mean(res_b2)).^2))
    append!(htau_bc_mse,mean((res_b5.-mean(res_b1)).^2))
end

writedlm("/home/users/yuchenhu/switchback/sim_mdp/sim_new/sim_b_10_80_l_30/result_T" * string(T) * ".csv",  [tau,tau_FATE,htau_dm_mse,htau_dmb_mse,htau_bc_mse], ',')
