$(document).ready(function() {
    let correctAnswers;
    try {
        correctAnswers = JSON.parse($('#taskData').attr('data-answers') || '[]');
    } catch (e) {
        console.error('Error parsing answers:', e);
        correctAnswers = [];
    }

    let questionsAnswered = new Array(correctAnswers.length).fill(false);

    function validateAnswer(input) {
        const answer = input.val().trim();
        const hint = input.siblings('.answer-hint');

        if (/[а-яА-ЯёЁ]/.test(answer)) {
            hint.text('Please use English letters only!').addClass('error');
            return false;
        }
        if (/^\d+$/.test(answer)) {
            hint.text('Numbers are not allowed!').addClass('error');
            return false;
        }
        if (answer !== answer.toUpperCase()) {
            hint.text('Please use CAPS LOCK!').addClass('error');
            return false;
        }

        hint.text('').removeClass('error');
        return true;
    }

    $('.submit-button').on('click', function() {
        const inputField = $(this).siblings('.answer');
        const index = $(this).parent().index();

        if (!validateAnswer(inputField)) return;

        const userAnswer = inputField.val().trim();

        if (index < correctAnswers.length) {
            questionsAnswered[index] = true;
            if (userAnswer.toUpperCase() === correctAnswers[index].toUpperCase()) {
                inputField.removeClass('incorrect').addClass('correct');
                $(this).siblings('.feedback').html('Верно!').show();
            } else {
                inputField.removeClass('correct').addClass('incorrect');
                $(this).siblings('.feedback').html('Неверно!').show();
            }
        }
    });

    $('.show-answer').on('click', function() {
        const allAnswered = questionsAnswered.every(answered => answered);
        if (!allAnswered) {
            alert('Сначала ответьте на все вопросы!');
            return;
        }
        $(this).siblings('.correct-answer').toggle();
    });

    $('#checkAnswers').on('click', function() {
        let score = 0;
        let allAnswered = true;

        $('.answer').each(function(index) {
            const userAnswer = $(this).val().trim();
            if (userAnswer === "") {
                allAnswered = false;
                return false;
            }
            if (userAnswer.toUpperCase() === correctAnswers[index].toUpperCase()) {
                score++;
            }
            questionsAnswered[index] = true;
        });

        if (!allAnswered) {
            alert('Пожалуйста, ответьте на все вопросы!');
            return;
        }

        $('#result').html(`<p>Вы набрали ${score} из ${correctAnswers.length} правильных ответов!</p>`);
    });
});