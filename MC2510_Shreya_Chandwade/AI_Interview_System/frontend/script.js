let questions = [];
let rounds = [];
let currentQuestion = 0;
let currentRound = 1;
let jobRole = "";
let interviewMode = "text";
let scores = [];
let evaluations = [];
let userAnswers = [];
let questionTypes = [];
let questionMeta = [];
let sentiments = [];
let idealAnswers = [];
let interviewResultId = "";
let resumeText = "";
let resumeSkills = [];
let isResumeLoaded = false;
let isRecording = false;
let recognition = null;
let synth = window.speechSynthesis;
let voiceTranscript = "";
let recognitionRestartPending = false;


// ----------------------------------
// Speech Recognition Setup
// ----------------------------------

function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return null;

    const rec = new SpeechRecognition();
    rec.continuous = false;
    rec.interimResults = true;
    rec.lang = "en-US";

    rec.onresult = (event) => {
        let interimTranscript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const text = event.results[i][0].transcript.trim();
            if (event.results[i].isFinal) {
                voiceTranscript = `${voiceTranscript} ${text}`.trim();
            } else {
                interimTranscript += ` ${text}`;
            }
        }
        const answer = document.getElementById("answer");
        answer.value = `${voiceTranscript}${interimTranscript}`.trim();
        document.getElementById("voiceStatus").textContent =
            isRecording ? "Listening..." : "Transcription complete. Review your answer below.";
    };

    rec.onerror = (event) => {
        const recoverable = ["no-speech", "aborted"].includes(event.error);
        document.getElementById("voiceStatus").textContent = recoverable
            ? "No speech detected. Press Start Speaking to try again."
            : `Microphone error: ${event.error || "permission unavailable"}`;
        isRecording = false;
        recognitionRestartPending = false;
        updateVoiceControls();
    };

    rec.onend = () => {
        recognitionRestartPending = false;
        if (isRecording) {
            isRecording = false;
            updateVoiceControls(false);
            document.getElementById("voiceStatus").textContent = "Transcription complete. Review your answer below.";
        }
    };

    return rec;
}


function toggleVoiceRecording() {
    if (!recognition) {
        recognition = initSpeechRecognition();
    }
    if (!recognition) {
        alert("Speech recognition is not supported in this browser. Please use Chrome.");
        return;
    }

    if (isRecording) {
        stopVoiceRecording();
    } else {
        startVoiceRecording();
    }
}


function startVoiceRecording() {
    if (!recognition) return;
    isRecording = true;
    voiceTranscript = document.getElementById("answer").value.trim();
    updateVoiceControls();
    document.getElementById("voiceStatus").textContent = "Listening... speak your answer";

    try {
        recognition.start();
    } catch (e) {
        isRecording = false;
        updateVoiceControls();
        document.getElementById("voiceStatus").textContent = "Microphone is already active. Try again in a moment.";
    }
}


function stopVoiceRecording() {
    isRecording = false;
    recognitionRestartPending = false;
    updateVoiceControls();
    document.getElementById("voiceStatus").textContent = "Recording stopped. Review your transcript below.";

    if (recognition) {
        try { recognition.stop(); } catch (e) { /* ok */ }
    }
}


function updateVoiceControls(showWaveform = isRecording) {
    const micBtn = document.getElementById("micButton");
    const waveform = document.getElementById("voiceWaveform");
    const micLabel = document.getElementById("micLabel");
    if (!micBtn || !waveform || !micLabel) return;
    micBtn.classList.toggle("recording", isRecording);
    micBtn.setAttribute("aria-pressed", String(isRecording));
    micLabel.textContent = isRecording ? "Stop Recording" : "Start Speaking";
    waveform.classList.toggle("hidden", !showWaveform);
}


function speakQuestion() {
    const text = questions[currentQuestion];
    if (!text || !synth) return;

    synth.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1;
    synth.speak(utterance);
}


// ----------------------------------
// Resume Upload & Processing
// ----------------------------------

async function uploadResumeFile(file) {
    if (!file || !file.name.toLowerCase().endsWith(".pdf")) {
        document.getElementById("setupError").textContent = "Please upload a PDF file.";
        return;
    }

    const error = document.getElementById("setupError");
    const processing = document.getElementById("resumeProcessing");
    const placeholder = document.getElementById("uploadPlaceholder");
    const results = document.getElementById("resumeResults");

    error.textContent = "";
    placeholder.classList.add("hidden");
    processing.classList.remove("hidden");
    results.classList.add("hidden");

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/upload-resume", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Resume upload failed.");

        resumeText = data.resume_text || "";
        resumeSkills = data.skills || [];
        isResumeLoaded = true;

        document.getElementById("jobRole").value = data.inferred_role || "";
        document.getElementById("skills").value = resumeSkills.join(", ");

        const expSelect = document.getElementById("experience");
        const expYears = data.experience_years || "";
        if (expYears.includes("0") || expYears.toLowerCase().includes("fresher")) {
            expSelect.value = "Fresher";
        } else if (expYears.startsWith("1") || expYears.startsWith("2")) {
            expSelect.value = "0-2 years";
        } else if (expYears.startsWith("3") || expYears.startsWith("4") || expYears.startsWith("5")) {
            expSelect.value = "2-5 years";
        } else {
            expSelect.value = "5+ years";
        }

        document.getElementById("resumeInferredRole").textContent = data.inferred_role || "—";
        document.getElementById("resumeExperience").textContent = data.experience_years || "—";
        document.getElementById("resumeSkillCount").textContent = resumeSkills.length;

        const tagsContainer = document.getElementById("resumeSkillsTags");
        tagsContainer.innerHTML = resumeSkills.map(skill =>
            `<span class="skill-tag">${skill}</span>`
        ).join("");

        const preview = document.getElementById("resumeTextPreview");
        if (preview) preview.textContent = data.text_preview || "";

        processing.classList.add("hidden");
        results.classList.remove("hidden");
        document.getElementById("resumeInterviewBtn").classList.remove("hidden");

    } catch (err) {
        processing.classList.add("hidden");
        placeholder.classList.remove("hidden");
        error.textContent = err.message || "Failed to process resume.";
    }
}


function handleResumeSelect(event) {
    const file = event.target.files[0];
    if (file) uploadResumeFile(file);
}


async function startResumeInterview() {
    if (!isResumeLoaded || !resumeText) {
        document.getElementById("setupError").textContent =
            "Please upload a resume first.";
        return;
    }

    const role = document.getElementById("jobRole").value.trim() || "Software Developer";
    const error = document.getElementById("setupError");
    error.textContent = "";
    jobRole = role;
    resetInterviewState();

    try {
        const response = await fetch("/generate-resume-questions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                resume_text: resumeText,
                skills: resumeSkills,
                job_role: role
            })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Failed to generate resume questions.");
        }

        const data = await response.json();
        applyInterviewData(data, true);

    } catch (err) {
        console.error("Resume interview error:", err);
        error.textContent = err.message || "Failed to start resume interview.";
    }
}


function applyInterviewData(data, isResume = false) {
    if (data.questions && Array.isArray(data.questions)) {
        rounds = data.rounds || [];
        questions = data.questions.map(q => typeof q === "string" ? q : q.text);
        questionMeta = data.questions.map(q =>
            typeof q === "string"
                ? { type: "text", round: 1, round_name: "Interview" }
                : q
        );
    } else if (data.questions && typeof data.questions === "string") {
        questions = parseQuestions(data.questions);
        questionMeta = questions.map(() => ({
            type: "text", round: 1, round_name: "Technical"
        }));
        rounds = [];
    } else {
        throw new Error("No questions were generated.");
    }

    if (questions.length === 0) throw new Error("No questions were generated.");

    questionTypes = questionMeta.map(q => q.type || "text");
    currentQuestion = 0;
    currentRound = questionMeta[0]?.round || 1;

    document.getElementById("setupSection").classList.add("hidden");
    document.getElementById("interviewSection").classList.remove("hidden");
    document.getElementById("jobRoleDisplay").textContent = jobRole;

    const stepper = document.getElementById("roundStepper");
    if (isResume) {
        stepper.classList.add("hidden");
    } else {
        stepper.classList.remove("hidden");
    }

    updateRoundStepper(currentRound);
    showQuestion();
}


function resetInterviewState() {
    questions = [];
    rounds = [];
    currentQuestion = 0;
    currentRound = 1;
    scores = [];
    evaluations = [];
    userAnswers = [];
    questionTypes = [];
    questionMeta = [];
    sentiments = [];
    idealAnswers = [];
    interviewResultId = "";
}

async function analyzeSkills() {
    const role = document.getElementById("jobRole").value.trim();
    const skills = document.getElementById("skills").value.trim();
    const experience = document.getElementById("experience").value;
    const error = document.getElementById("setupError");
    const analysisBox = document.getElementById("skillAnalysis");

    if (!role || !skills) {
        error.textContent = "Please enter job role and skills before analysis.";
        return;
    }

    error.textContent = "";
    analysisBox.textContent = "AI is analyzing your skill profile...";
    analysisBox.classList.remove("hidden");

    try {
        const response = await fetch("/analyze-skills", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ job_role: role, skills, experience })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Skill analysis failed.");
        analysisBox.textContent = data.analysis;
    } catch (err) {
        analysisBox.textContent = err.message || "Failed to analyze skills.";
    }
}


// ----------------------------------
// Start Interview
// ----------------------------------

async function startInterview() {
    const role = document.getElementById("jobRole").value.trim();
    const skills = document.getElementById("skills").value.trim();
    const experience = document.getElementById("experience").value;
    interviewMode = document.getElementById("interviewMode").value;
    const error = document.getElementById("setupError");

    if (!role || !skills) {
        error.textContent = "Please enter job role and skills.";
        return;
    }

    error.textContent = "";
    jobRole = role;
    const startBtn = document.getElementById("startInterviewBtn");
    if (startBtn) {
        startBtn.disabled = true;
        startBtn.textContent = "Generating questions...";
    }
    resetInterviewState();

    try {
        const response = await fetch("/generate-questions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                job_role: role,
                skills,
                experience,
                interview_mode: interviewMode,
                multi_round: true,
                difficulty: document.getElementById("difficulty")?.value || "",
                question_count: Number(document.getElementById("questionCount")?.value || 0)
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server error (${response.status}): ${errorText}`);
        }

        const data = await response.json();

        applyInterviewData(data, false);

    } catch (err) {
        console.error("Interview start error:", err);
        error.textContent = err.message || "Failed to generate questions.";
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.textContent = "Start interview";
        }
    }
}


function parseQuestions(text) {
    if (!text) return [];
    return text
        .split("\n")
        .map(line => line.replace(/^\s*\d+[\.\)]\s*/, "").trim())
        .filter(line => line.length > 0);
}


// ----------------------------------
// Round Stepper
// ----------------------------------

function updateRoundStepper(roundNum) {
    document.querySelectorAll(".round-step").forEach(step => {
        const r = parseInt(step.dataset.round);
        step.classList.remove("active", "completed");
        if (r < roundNum) step.classList.add("completed");
        else if (r === roundNum) step.classList.add("active");
    });
}


// ----------------------------------
// Display Question
// ----------------------------------

function showQuestion() {
    const meta = questionMeta[currentQuestion] || {};
    const qType = meta.type || questionTypes[currentQuestion] || "text";
    const roundNum = meta.round || 1;
    const roundName = meta.round_name || "Interview";

    currentRound = roundNum;
    updateRoundStepper(roundNum);

    document.getElementById("question").textContent = questions[currentQuestion];
    document.getElementById("questionNumber").textContent =
        `Question ${currentQuestion + 1} of ${questions.length}`;

    const progress = ((currentQuestion + 1) / questions.length) * 100;
    document.getElementById("progressBar").style.width = `${progress}%`;

    document.getElementById("roundBadge").textContent =
        `Round ${roundNum} · ${roundName}`;

    const typeBadge = document.getElementById("questionTypeBadge");
    typeBadge.textContent = qType.charAt(0).toUpperCase() + qType.slice(1);
    typeBadge.className = "badge badge-" + qType;

    // Show/hide panels based on question type
    const voicePanel = document.getElementById("voicePanel");
    const textPanel = document.getElementById("textAnswerPanel");
    const codingPanel = document.getElementById("codingPanel");

    voicePanel.classList.add("hidden");
    textPanel.classList.remove("hidden");
    codingPanel.classList.add("hidden");

    const voiceModeActive = interviewMode === "voice" || interviewMode === "mixed";
    if (qType === "voice" || (voiceModeActive && qType !== "coding")) {
        voicePanel.classList.remove("hidden");
        textPanel.classList.remove("hidden");
    }

    if (qType === "coding") {
        textPanel.classList.add("hidden");
        codingPanel.classList.remove("hidden");

        const starterCode = meta.starter_code || "";
        document.getElementById("codeEditor").value = starterCode;
        document.getElementById("codeLanguage").textContent =
            (meta.language || "python").toUpperCase();

        const testCases = meta.test_cases || [];
        const testInfo = document.getElementById("testCaseInfo");
        if (testCases.length > 0) {
            testInfo.innerHTML = "<strong>Sample test cases:</strong><br>" +
                testCases.slice(0, 2).map(tc =>
                    `Input: ${JSON.stringify(tc.input)} → Expected: ${JSON.stringify(tc.expected)}`
                ).join("<br>");
        } else {
            testInfo.textContent = "";
        }
    } else {
        document.getElementById("answer").value = "";
    }

    if (qType !== "coding") {
        voiceTranscript = "";
        updateVoiceControls(false);
    }

    const prevButton = document.getElementById("prevButton");
    if (prevButton) prevButton.disabled = currentQuestion === 0;

    const storedAnswer = userAnswers[currentQuestion] || "";
    if (qType === "coding") {
        if (storedAnswer) document.getElementById("codeEditor").value = storedAnswer;
    } else if (storedAnswer) {
        document.getElementById("answer").value = storedAnswer;
    }

    const button = document.getElementById("submitButton");
    if (evaluations[currentQuestion]) {
        document.getElementById("evaluationText").textContent = evaluations[currentQuestion];
        document.getElementById("evaluation").classList.remove("hidden");
        const storedIdeal = idealAnswers[currentQuestion];
        document.getElementById("idealAnswerPanel").classList.toggle("hidden", !storedIdeal);
        if (storedIdeal) document.getElementById("idealAnswerText").textContent = storedIdeal;
        const storedSentiment = sentiments[currentQuestion];
        const sentimentPanel = document.getElementById("sentimentPanel");
        if (storedSentiment) {
            sentimentPanel.classList.remove("hidden");
            document.getElementById("sentimentValue").textContent = `${storedSentiment.sentiment_label} (${storedSentiment.sentiment_score}%)`;
            document.getElementById("confidenceValue").textContent = `${storedSentiment.confidence_score}%`;
            document.getElementById("questionScoreValue").textContent = `${Math.round(scores[currentQuestion] || 0)}%`;
        } else {
            sentimentPanel.classList.add("hidden");
        }
        button.classList.add("hidden");
    } else {
        document.getElementById("evaluation").classList.add("hidden");
        document.getElementById("sentimentPanel").classList.add("hidden");
        document.getElementById("idealAnswerPanel").classList.add("hidden");
        button.classList.remove("hidden");
        button.disabled = false;
        button.textContent = qType === "coding" ? "Submit Code" : "Submit Answer";
    }

    if (qType === "voice" && interviewMode !== "text") {
        setTimeout(() => speakQuestion(), 500);
    }
}


// ----------------------------------
// Submit Answer
// ----------------------------------

async function submitAnswer() {
    const meta = questionMeta[currentQuestion] || {};
    const qType = meta.type || questionTypes[currentQuestion] || "text";

    if (isRecording) stopVoiceRecording();

    let answer = "";
    if (qType === "coding") {
        answer = document.getElementById("codeEditor").value.trim();
    } else {
        answer = document.getElementById("answer").value.trim();
    }

    if (!answer) {
        alert(qType === "coding" ? "Please write your code." : "Please enter your answer.");
        return;
    }

    const question = questions[currentQuestion];
    const button = document.getElementById("submitButton");
    button.disabled = true;
    button.textContent = "AI is evaluating...";

    try {
        let data;

        if (qType === "coding") {
            const response = await fetch("/evaluate-coding", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    job_role: jobRole,
                    question,
                    code: answer,
                    test_cases: meta.test_cases || []
                })
            });
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server error (${response.status}): ${errorText}`);
            }
            data = await response.json();
        } else {
            const response = await fetch("/evaluate-answer", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    job_role: jobRole,
                    question,
                    answer,
                    question_type: qType,
                    ideal_answer_hint: meta.ideal_answer || ""
                })
            });
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server error (${response.status}): ${errorText}`);
            }
            data = await response.json();
        }

        const evaluation = data.evaluation;
        let score = typeof data.score === "number" ? data.score : 0;

        if (!score) {
            const scoreMatch = evaluation.match(/Score:\s*(\d+(?:\.\d+)?)\s*\/\s*10/i);
            if (scoreMatch) score = parseFloat(scoreMatch[1]) * 10;
        }

        userAnswers[currentQuestion] = answer;
        scores[currentQuestion] = score;
        evaluations[currentQuestion] = evaluation;
        sentiments[currentQuestion] = data.sentiment || null;
        idealAnswers[currentQuestion] = data.ideal_answer || meta.ideal_answer || "";

        document.getElementById("evaluationText").textContent = evaluation;

        const idealPanel = document.getElementById("idealAnswerPanel");
        const idealText = idealAnswers[currentQuestion];
        if (idealText) {
            idealPanel.classList.remove("hidden");
            document.getElementById("idealAnswerText").textContent = idealText;
        } else {
            idealPanel.classList.add("hidden");
        }

        // Sentiment panel
        const sentimentPanel = document.getElementById("sentimentPanel");
        if (data.sentiment) {
            sentimentPanel.classList.remove("hidden");
            document.getElementById("sentimentValue").textContent =
                `${data.sentiment.sentiment_label} (${data.sentiment.sentiment_score}%)`;
            document.getElementById("confidenceValue").textContent =
                `${data.sentiment.confidence_score}%`;
            document.getElementById("questionScoreValue").textContent =
                `${Math.round(score)}%`;
        } else {
            sentimentPanel.classList.add("hidden");
        }

        document.getElementById("evaluation").classList.remove("hidden");
        button.classList.add("hidden");

    } catch (err) {
        console.error("Answer evaluation error:", err);
        alert(err.message || "Failed to evaluate answer.");
    } finally {
        button.disabled = false;
        button.textContent = qType === "coding" ? "Submit Code" : "Submit Answer";
    }
}


// ----------------------------------
// Next Question / Round Transition
// ----------------------------------

function previousQuestion() {
    if (currentQuestion <= 0) return;
    currentQuestion -= 1;
    showQuestion();
}


function nextQuestion() {
    const meta = questionMeta[currentQuestion] || {};
    const currentRoundNum = meta.round || 1;

    currentQuestion++;

    if (currentQuestion >= questions.length) {
        finishInterview();
        return;
    }

    const nextMeta = questionMeta[currentQuestion] || {};
    const nextRoundNum = nextMeta.round || 1;

    if (nextRoundNum > currentRoundNum) {
        showRoundTransition(currentRoundNum, nextRoundNum);
        return;
    }

    showQuestion();
}


function showRoundTransition(completedRound, nextRound) {
    document.getElementById("interviewSection").classList.add("hidden");
    document.getElementById("roundTransition").classList.remove("hidden");

    const roundNames = { 1: "Technical", 2: "Coding", 3: "HR & Behavioral" };
    document.getElementById("roundCompleteTitle").textContent =
        `Round ${completedRound} Complete!`;

    const nextName = roundNames[nextRound] || `Round ${nextRound}`;
    document.getElementById("roundCompleteMsg").textContent =
        `Great progress! Next up: ${nextName}`;

    const roundScores = [];
    questionMeta.forEach((m, i) => {
        if ((m.round || 1) === completedRound && scores[i] !== undefined) {
            roundScores.push(scores[i]);
        }
    });

    const avg = roundScores.length
        ? Math.round(roundScores.reduce((a, b) => a + b, 0) / roundScores.length)
        : 0;

    document.getElementById("roundScoreSummary").innerHTML =
        `<div class="round-avg-score">Round ${completedRound} Average: <strong>${avg}%</strong></div>`;
}


function continueToNextRound() {
    document.getElementById("roundTransition").classList.add("hidden");
    document.getElementById("interviewSection").classList.remove("hidden");
    showQuestion();
}


function finishInterview() {
    document.getElementById("interviewSection").classList.add("hidden");
    document.getElementById("roundTransition").classList.add("hidden");
    document.getElementById("resultSection").classList.remove("hidden");
    showFinalReport();
}


// ----------------------------------
// Final Report
// ----------------------------------

async function showFinalReport() {
    const token = localStorage.getItem("access_token");

    let feedback = "";
    if (questions.length > 0) {
        interviewResultId = interviewResultId || (window.crypto?.randomUUID?.() || `interview-${Date.now()}`);
    }

    let totalScore = 0;
    let validScores = 0;
    scores.forEach(score => {
        if (typeof score === "number" && !isNaN(score)) {
            totalScore += score;
            validScores++;
        }
    });

    const percentage = validScores > 0 ? Math.round(totalScore / validScores) : 0;
    if (token && questions.length > 0) {
        const saveStatus = document.getElementById("fusedDatasetSaveStatus");
        feedback = await loadAiInterviewFeedback(percentage);
        const answersData = questions.map((q, idx) => ({
            question: q,
            answer: userAnswers[idx] || "",
            evaluation: evaluations[idx] || "",
            score: scores[idx] !== undefined ? scores[idx] : 0,
            question_type: questionMeta[idx]?.type || "text",
            round: questionMeta[idx]?.round || 1,
            sentiment_score: sentiments[idx]?.sentiment_score,
            confidence_score: sentiments[idx]?.confidence_score,
            sentiment_label: sentiments[idx]?.sentiment_label,
            ideal_answer: idealAnswers[idx] || "",
            difficulty: questionMeta[idx]?.difficulty || "",
        }));

        fetch("/save-interview", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({
                result_id: interviewResultId,
                job_role: jobRole || "General",
                skills: document.getElementById("skills")?.value.trim() || "",
                experience: document.getElementById("experience")?.value || "",
                interview_mode: interviewMode,
                total_rounds: rounds.length || 3,
                answers: answersData,
                feedback,
                skill_gap: document.getElementById("skillAnalysis")?.textContent?.trim() || "",
                performance: percentage >= 80 ? "Excellent" : percentage >= 60 ? "Good" : "Needs Practice",
                difficulty: document.getElementById("difficulty")?.value || ""
            })
        }).then(async response => {
            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || "Could not save fused dataset record.");
            }
            const saved = await response.json();
            if (saved.interview_id) localStorage.setItem("last_interview_id", String(saved.interview_id));
            if (saveStatus) saveStatus.textContent = "";
            localStorage.setItem("fused_dataset_refresh", Date.now().toString());
        }).catch(err => {
            if (saveStatus) {
                saveStatus.classList.remove("hidden");
                saveStatus.textContent = `Could not save this interview: ${err.message}`;
            }
            console.error("Auto-save error:", err);
        });
    }
    document.getElementById("overallScore").textContent = `${percentage}%`;
    const overallProgressBar = document.getElementById("overallProgressBar");
    if (overallProgressBar) overallProgressBar.style.width = `${Math.max(0, Math.min(100, percentage))}%`;
    const scoredAnswerCount = document.getElementById("scoredAnswerCount");
    if (scoredAnswerCount) scoredAnswerCount.textContent = `${validScores} / ${questions.length}`;
    const bestAnswerScore = document.getElementById("bestAnswerScore");
    if (bestAnswerScore) bestAnswerScore.textContent = `${validScores ? Math.round(Math.max(...scores.filter(score => typeof score === "number" && !isNaN(score)))) : 0}%`;

    // Round-wise summary
    const roundResults = document.getElementById("roundResultsSummary");
    const roundMap = {};
    questionMeta.forEach((m, i) => {
        const r = m.round || 1;
        if (!roundMap[r]) roundMap[r] = { name: m.round_name || `Round ${r}`, scores: [] };
        if (scores[i] !== undefined) roundMap[r].scores.push(scores[i]);
    });

    roundResults.innerHTML = Object.entries(roundMap).map(([r, data]) => {
        const avg = data.scores.length
            ? Math.round(data.scores.reduce((a, b) => a + b, 0) / data.scores.length)
            : 0;
        return `<div class="round-result-card">
            <div class="round-result-copy"><span>${data.name}</span><small>${data.scores.length} answer${data.scores.length === 1 ? "" : "s"}</small></div>
            <div class="round-result-score"><strong>${avg}%</strong><div class="round-progress-track"><div class="round-progress-fill" style="width: ${Math.max(0, Math.min(100, avg))}%"></div></div></div>
        </div>`;
    }).join("");
    const completedRoundCount = document.getElementById("completedRoundCount");
    if (completedRoundCount) completedRoundCount.textContent = Object.keys(roundMap).length;

    const scoreList = document.getElementById("scoreList");
    scoreList.innerHTML = "";
    questions.forEach((question, index) => {
        const score = typeof scores[index] === "number" && !isNaN(scores[index]) ? scores[index] : 0;
        const meta = questionMeta[index] || {};
        const item = document.createElement("div");
        item.className = "score-item";
        item.innerHTML = `
            <div class="score-question-copy"><strong>Q${index + 1}</strong><span>${meta.round_name || "Round"} · ${meta.type || "text"}</span></div>
            <div class="answer-score-visual"><div class="answer-score-row"><span class="score-badge ${score >= 80 ? 'high' : score >= 60 ? 'medium' : 'low'}">${Math.round(score)}%</span><strong>${score >= 80 ? "Strong" : score >= 60 ? "Developing" : "Needs focus"}</strong></div><div class="answer-progress-track"><div class="answer-progress-fill ${score >= 80 ? 'high' : score >= 60 ? 'medium' : 'low'}" style="width: ${Math.max(0, Math.min(100, score))}%"></div></div></div>
            <small>${sentiments[index]?.sentiment_label || "Evaluation complete"}</small>
        `;
        scoreList.appendChild(item);
    });

    const feedbackSummary = document.getElementById("feedbackSummary");
    let msg = percentage >= 80
        ? "Excellent performance across all rounds!"
        : percentage >= 60
            ? "Good performance! Review coding and HR responses."
            : percentage >= 40
                ? "Average performance. Focus on technical fundamentals and communication."
                : "More preparation needed. Use the study plan on your dashboard.";

    feedbackSummary.innerHTML = `
        <div class="result-box">
            <p>Completed <strong>${questions.length}</strong> questions across <strong>${Object.keys(roundMap).length}</strong> rounds.</p>
            <p>Average score: <strong>${percentage}%</strong></p>
            <p>Mode: <strong>${interviewMode}</strong></p>
            <p>${msg}</p>
        </div>`;

}


async function loadAiInterviewFeedback(percentage) {
    const feedbackBox = document.getElementById("aiFeedbackSummary");
    if (!feedbackBox) return "";

    feedbackBox.textContent = "Generating detailed AI feedback summary...";
    feedbackBox.classList.remove("hidden");

    try {
        const response = await fetch("/interview-feedback", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                job_role: jobRole || "General",
                skills: document.getElementById("skills")?.value.trim() || "",
                overall_score: percentage,
                answers: questions.map((q, idx) => ({
                    question: q,
                    answer: userAnswers[idx] || "",
                    score: scores[idx] !== undefined ? scores[idx] : 0
                }))
            })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Failed.");
        feedbackBox.textContent = data.feedback;
        return data.feedback || "";
    } catch (err) {
        feedbackBox.textContent = err.message || "Could not load AI feedback.";
        return "";
    }
}


// ----------------------------------
// Restart
// ----------------------------------

async function restartInterview() {
    const ok = await App.confirm("Start another interview? This screen will return to setup.");
    if (!ok) return;
    resetInterviewState();
    if (isRecording) stopVoiceRecording();
    if (synth) synth.cancel();

    document.getElementById("resultSection").classList.add("hidden");
    document.getElementById("interviewSection").classList.add("hidden");
    document.getElementById("roundTransition").classList.add("hidden");
    document.getElementById("setupSection").classList.remove("hidden");
    document.getElementById("roundStepper").classList.remove("hidden");

    document.getElementById("jobRole").value = "";
    document.getElementById("skills").value = "";
    document.getElementById("experience").selectedIndex = 0;
    document.getElementById("interviewMode").selectedIndex = 0;
    document.getElementById("setupError").textContent = "";

    resumeText = "";
    resumeSkills = [];
    isResumeLoaded = false;
    document.getElementById("resumeResults").classList.add("hidden");
    document.getElementById("uploadPlaceholder").classList.remove("hidden");
    document.getElementById("resumeProcessing").classList.add("hidden");
    document.getElementById("resumeInterviewBtn").classList.add("hidden");
    document.getElementById("resumeFile").value = "";

    const skillAnalysis = document.getElementById("skillAnalysis");
    if (skillAnalysis) {
        skillAnalysis.textContent = "";
        skillAnalysis.classList.add("hidden");
    }

    const aiFeedback = document.getElementById("aiFeedbackSummary");
    if (aiFeedback) {
        aiFeedback.textContent = "";
        aiFeedback.classList.add("hidden");
    }
}


document.addEventListener("DOMContentLoaded", () => {
    recognition = initSpeechRecognition();

    const dropZone = document.getElementById("resumeDropZone");
    if (dropZone) {
        dropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropZone.classList.add("drag-over");
        });
        dropZone.addEventListener("dragleave", () => {
            dropZone.classList.remove("drag-over");
        });
        dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropZone.classList.remove("drag-over");
            const file = e.dataTransfer.files[0];
            if (file) uploadResumeFile(file);
        });
    }

    const token = localStorage.getItem("access_token");
    const navLinks = document.getElementById("navLinks");
    if (token && navLinks) {
        const loginLink = document.getElementById("loginLink");
        const registerLink = document.getElementById("registerLink");
        if (loginLink) loginLink.style.display = "none";
        if (registerLink) registerLink.style.display = "none";

        const logoutA = document.createElement("a");
        logoutA.href = "#";
        logoutA.textContent = "Logout";
        logoutA.onclick = (e) => {
            e.preventDefault();
            localStorage.removeItem("access_token");
            localStorage.removeItem("user");
            window.location.reload();
        };
        navLinks.appendChild(logoutA);
    }
});
