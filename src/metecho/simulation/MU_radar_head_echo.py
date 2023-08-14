def simulate_head_echo(t, model, pulses, experiment, radar, noise_sigma):
    
    ipp_len = length(ipp)
    ipp_total = max(ipp) + min(ipp) - 1

    [position, velocity] = model.evaluate((ipp - min(ipp))*radar.experiment["T_ipp"])

    k_vectors = zeros(3, ipp_len)
    DATA_r = zeros(1, ipp_len)
    az = zeros(1, ipp_len)
    el = zeros(1, ipp_len)
    for i=1:ipp_len
        k_vectors(:,i) = position(:,i)./norm(position(:,i))
        k = k_vectors(:,i)
        az(i) = mod(pi/2 - atan2(k(2),k(1))+2*pi,2*pi)
        el(i) = acos( sqrt(k(1).^2 + k(2).^2) )
        DATA_r(i) = norm(position(:,i))
    end
    
    DATA_Gi_r = zeros(1,ipp_len)
    DATA_vel = zeros(1,ipp_len)
    DATA_vel_full = zeros(1,ipp_len)
    DATA_vel_angle = zeros(1,ipp_len)
    for i=1:ipp_len
        DATA_vel_full(i) = norm(velocity(:,i))
        direction = velocity(:,i)./norm(velocity(:,i))
        rad_ang = atan2(norm(cross(position(:, i),direction)),dot(position(:, i),direction))

        if rad_ang > pi/2
            vel_ang = pi - rad_ang
        else
            vel_ang = rad_ang
        end
        DATA_vel_angle(i) = vel_ang
        DATA_vel(i) = norm(velocity(:,i))*cos(vel_ang)
    end
    
    DATA_dop_hz = 2*DATA_vel*radar.f/constants.c
    DATA_dop = 2*pi*DATA_dop_hz
    
    DATA_f = zeros(1,ipp_len)
    for i=1:ipp_len
        DATA_f(i) = ( 2.0*norm(position(:,i))/constants.c - radar.experiment["T_samp_start"] ) / radar.experiment["T_samp"]
    end
    DATA_n = floor(DATA_f)
    
    power = zeros(size(ipp))
    phase = zeros(size(ipp))
    amplit = zeros(size(ipp))
    code_enchance = zeros(size(ipp))
    
    amp3 = zeros(radar.beam.channels, radar.experiment["N_measure,"] ipp_total)
    
    ipp_cnt = 0
    for i=1:ipp_total
        if sum(i==ipp) == 1
            ipp_cnt = ipp_cnt + 1

            delta = mod(DATA_f(ipp_cnt),1)
            frac_s = 1 - delta

            code28 = [0 radar.experiment["code"] 0 ]
            code27 = interp1q((1:length(code28))', code28', ((1+frac_s-floor(frac_s)):(length(code28)-1+frac_s-floor(frac_s)) )')'
            
            %time component of wave needs to change as sampling of wave
            %changes with range-gate sampling
            t = (DATA_n(ipp_cnt) + (0:radar.experiment["Bits))*radar.experiment["T_samp"]"]
            t0 = 2*DATA_r(ipp_cnt)/constants.c

            Amplitude = amplitude_curve(i)

            t_cnt = 0
            subs = zeros(1,length(t))
            
            carrier_signal = radar.beam.gain(k_vectors(:,ipp_cnt))
            DATA_Gi_r(ipp_cnt) = abs(radar.full_beam.gain(k_vectors(:,ipp_cnt)))
            if normalize_gain == 1
                carrier_signal = exp(1i*angle(carrier_signal))
            end
            
            for j=1:radar.experiment["N_measure"]
                noise = (randn(radar.beam.channels,1) + 1i*randn(radar.beam.channels,1))*noise_sigma
                
                if j >= (DATA_n(ipp_cnt)+1) && j <= (DATA_n(ipp_cnt) + radar.experiment["N_code)"]
                    t_cnt = t_cnt + 1
                    
                    phi = DATA_dop(ipp_cnt)*t(t_cnt) - t0*radar.omega
                    experiment["signal"] = code27(t_cnt)*exp( -1i*phi )
                    
                    signal = carrier_signal.*experiment["signal*Amplitude"]
                    
                    subs(t_cnt) = sum(signal)
                    
                    amp3(:,j,i) = signal + noise
                    
                    
                else
                    amp3(:,j,i) = noise
                end

            end
            

            phase(ipp_cnt) = angle(mean(subs.*conj(code27.*exp(-1i*DATA_dop(ipp_cnt)*t))))
            %phase(ipp_cnt) = mod(t0*radar.omega, 2*pi) - pi
            power(ipp_cnt) = mean((subs./code27).*conj(subs./code27))
            amplit(ipp_cnt) = Amplitude*DATA_Gi_r(ipp_cnt)
            code_enchance(ipp_cnt) = sum(abs(code27).^2)

        else
            amp3(:,:,i) = (randn(radar.beam.channels,radar.experiment["N_measure)"] + 1i*randn(radar.beam.channels,radar.experiment["N_measure))*noise_sigma"]
        end
    end
    
    raw_data.amp3 = amp3
    raw_data.radar = radar
    raw_data.date = the_date
    raw_data.t = (1:ipp_total)*radar.experiment["T_ipp"]

    meteor.used_indecies = ones(size(ipp)) == 1
    meteor.ipp = ipp
    meteor.doppler_freq = -DATA_dop/(2*pi)
    meteor.doppler_vel = DATA_vel
    meteor.start_index = DATA_f + 1
    meteor.k_vector = k_vectors
    meteor.range = DATA_r
    
    meteor.beam_angle = DATA_vel_angle

    meteor.velocity = DATA_vel_full
    meteor.LOS_velocity = zeros(size(DATA_vel))
    meteor.LOS_velocity(1:(end-1)) = (DATA_vel(1:(end-1)) + DATA_vel(2:end))*0.5
    meteor.LOS_velocity(end) = nan

    meteor.azimuth = az
    meteor.elevation = el

    meteor.height = position(3,:)
    meteor.position = position

    meteor.power = power
    meteor.phase = phase

    meteor.SNR = amplit.^2.*radar.experiment["Bits/(2*radar.beam.channels*noise_sigma^2)"]
    meteor.SNRdB = 10*log10(meteor.SNR)
    
    meteor.channel_SNR = amplitude_curve(ipp).^2/(2*noise_sigma^2)
    meteor.channel_SNRdB = 10*log10(meteor.channel_SNR)
    
    meteor.signal_amplitude = amplit
    meteor.wave_amplitude = amplitude_curve(ipp)
    meteor.noise = struct
    meteor.noise.sigma = noise_sigma
    
    T_sky = meteor_analysis.noise.noise_sigma_to_noise_temperature(noise_sigma, radar)
    meteor.noise.sky_noise_temperature = T_sky %K
    
    meteor.SNR = meteor.SNR(:).'
    meteor.SNRdB = meteor.SNRdB(:).'
    meteor.channel_SNR = meteor.channel_SNR(:).'
    meteor.channel_SNRdB = meteor.channel_SNRdB(:).'
    meteor.signal_amplitude = meteor.signal_amplitude(:).'
    meteor.wave_amplitude = meteor.wave_amplitude(:).'
    
    meteor.T_ipp = radar.experiment["T_ipp"]
    meteor.model = model
    
    meteor = meteor_analysis.noise.calculate_rcs(...
        radar, ...
        meteor, ...
        'polarization_factor', 1, ...
        'use_model', true, ...
        'sky_noise_temperature', meteor.noise.sky_noise_temperature, ...
        'beamformed_data', false ...
    )
    

end


function amp = parabolic_amp(inds, max_amp, ipp)
    amp = zeros(size(inds))
    width = max(ipp) - min(ipp)
    mid_ipp = 0.5*(min(ipp) + max(ipp))
    
    for i=1:length(inds)
        ind = inds(i)
        if ~(ind < min(ipp) || ind > max(ipp))
            amp(i) = max_amp - (ind - mid_ipp)^2*(max_amp/(width*0.5)^2)
        end
    end

end