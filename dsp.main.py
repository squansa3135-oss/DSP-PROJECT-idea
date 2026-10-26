clc;
clear;
close all;
rng(1);

%% 1. PARAMETERS
Fs = 8000;
f0 = 700;
unitTime = 0.10;
U = round(unitTime*Fs);
amplitude = 0.8;
SNR = 15;

message = upper(input('Enter text to transmit: ','s'));
message = regexprep(message,'[^A-Z0-9 ]','');
message = regexprep(strtrim(message),'\s+',' ');

%% 2. MORSE CODE TRANSLATION TABLE
letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';

codes = {'.-', '-...', '-.-.', '-..', '.', '..-.', '--.', '....', ...
'..', '.---', '-.-', '.-..', '--', '-.', '---', '.--.', '--.-', ...
'.-.', '...', '-', '..-', '...-', '.--', '-..-', '-.--', '--..', ...
'-----', '.----', '..---', '...--', '....-', '.....', '-....', ...
'--...', '---..', '----.'};

morseMap = containers.Map('KeyType','char','ValueType','char');
reverseMap = containers.Map('KeyType','char','ValueType','char');

for k = 1:length(letters)
    morseMap(letters(k)) = codes{k};
    reverseMap(codes{k}) = letters(k);
end

%% 3. TEXT TO MORSE CODE
morseText = '';
words = strsplit(message,' ');

for w = 1:length(words)
    word = words{w};

    for c = 1:length(word)
        morseText = [morseText morseMap(word(c))];

        if c < length(word)
            morseText = [morseText ' / '];
        end
    end

    if w < length(words)
        morseText = [morseText '   /   '];
    end
end

fprintf('\nOriginal Text: %s\n',message);
fprintf('Morse Code:    %s\n',morseText);

%% 4. GENERATE AUDIO FROM MORSE CODE
tx = zeros(1,3*U);

for w = 1:length(words)
    word = words{w};

    for c = 1:length(word)
        symbols = morseMap(word(c));

        for s = 1:length(symbols)

            if symbols(s) == '.'
                duration = U;
            else
                duration = 3*U;
            end

            n = 0:duration-1;
            tone = amplitude*sin(2*pi*f0*n/Fs);
            tx = [tx tone];

            % Gap between symbols
            if s < length(symbols)
                tx = [tx zeros(1,U)];
            end
        end

        % Gap between letters
        if c < length(word)
            tx = [tx zeros(1,3*U)];
        end
    end

    % Gap between words
    if w < length(words)
        tx = [tx zeros(1,7*U)];
    end
end

tx = [tx zeros(1,3*U)];
t = (0:length(tx)-1)/Fs;

%% 5. ADD NOISE
signalPower = mean(tx.^2);
noisePower = signalPower/(10^(SNR/10));
rx = tx + sqrt(noisePower)*randn(size(tx));

%% 6. BAND-PASS FILTER USING FFT
N = length(rx);
freq = (-floor(N/2):ceil(N/2)-1)*(Fs/N);

X = fftshift(fft(rx));
passband = abs(abs(freq)-f0) <= 250;
filtered = real(ifft(ifftshift(X.*passband)));

%% 7. ENVELOPE DETECTION
smoothLength = round(0.008*Fs);
envelope = conv(abs(filtered),ones(1,smoothLength)/smoothLength,'same');

threshold = median(envelope) + ...
    0.35*(max(envelope)-median(envelope));

active = envelope > threshold;

%% 8. DETECT DOTS AND DASHES
edges = diff([false active false]);
starts = find(edges == 1);
ends = find(edges == -1)-1;

detectedMorse = '';
letterCode = '';

for p = 1:length(starts)

    duration = ends(p)-starts(p)+1;

    if duration < 2*U
        letterCode = [letterCode '.'];
    else
        letterCode = [letterCode '-'];
    end

    if p < length(starts)
        gap = starts(p+1)-ends(p)-1;

        if gap >= 2*U
            detectedMorse = [detectedMorse letterCode ' / '];
            letterCode = '';

            if gap >= 5*U
                detectedMorse = [detectedMorse '/ '];
            end
        end
    end
end

if ~isempty(letterCode)
    detectedMorse = [detectedMorse letterCode];
end

fprintf('\nDetected Morse Code:\n%s\n',detectedMorse);

%% 9. MORSE CODE TO TEXT
% Decode individual letter groups.
% A slash separates letters; a double slash represents a word gap.
parts = regexp(strtrim(detectedMorse),'\s*/\s*','split');
decodedText = '';

for k = 1:length(parts)
    token = strtrim(parts{k});

    if isempty(token)
        continue;
    end

    if all(token == '/' )
        decodedText = [decodedText ' '];
    elseif isKey(reverseMap,token)
        decodedText = [decodedText reverseMap(token)];
    else
        decodedText = [decodedText '?'];
    end
end

decodedText = strtrim(decodedText);
fprintf('\nRecovered Text: %s\n',decodedText);

%% 10. PLOT SIGNALS
figure('Name','Morse Code Audio Communication');

subplot(3,1,1);
plot(t,tx);
title('Transmitted Morse Audio');
xlabel('Time (s)');
ylabel('Amplitude');
grid on;

subplot(3,1,2);
plot(t,rx);
title('Received Audio with Noise');
xlabel('Time (s)');
ylabel('Amplitude');
grid on;

subplot(3,1,3);
plot(t,filtered);
title('Filtered Audio');
xlabel('Time (s)');
ylabel('Amplitude');
grid on;

%% 11. PLOT ENVELOPE AND THRESHOLD
figure('Name','Morse Detection');

plot(t,envelope);
hold on;
yline(threshold,'r--','Threshold');
xlabel('Time (s)');
ylabel('Envelope');
title('Tone Detection Using Thresholding');
grid on;

%% 12. DISPLAY TRANSLATION RESULTS
fprintf('\n========== TRANSLATION RESULTS ==========\n');
fprintf('Input Text:       %s\n',message);
fprintf('Encoded Morse:    %s\n',morseText);
fprintf('Recovered Text:   %s\n',decodedText);

%% 13. PLAY AND SAVE AUDIO
sound(tx,Fs);
audiowrite('Morse_Audio.wav',tx(:),Fs);

disp('Audio saved as Morse_Audio.wav');
