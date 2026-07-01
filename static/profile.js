const avatarBtn = document.getElementById('avatarButton');
const dropdownMenu = document.getElementById('dropdownMenu');

if (avatarBtn && dropdownMenu) {
    document.addEventListener('click', function (e) {
        const isClickInside = avatarBtn.contains(e.target) || dropdownMenu.contains(e.target);

        if (avatarBtn.contains(e.target)) {
            dropdownMenu.classList.toggle('opacity-0');
            dropdownMenu.classList.toggle('scale-95');
            dropdownMenu.classList.toggle('pointer-events-none');
        } else if (!isClickInside) {
            dropdownMenu.classList.add('opacity-0', 'scale-95', 'pointer-events-none');
        }
    });
}

function profileLocale() {
    return (typeof getLang === 'function' && getLang() === 'tr') ? 'tr-TR' : 'en-US';
}

function formatTimeAgo(isoDate) {
    if (!isoDate) return t('profile.unknown');
    const completed = new Date(isoDate);
    const now = new Date();
    const diffMs = now - completed;
    const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (days > 0) return tFormat('profile.daysAgo', { n: days });
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    if (hours > 0) return tFormat('profile.hoursAgo', { n: hours });
    const minutes = Math.floor(diffMs / (1000 * 60));
    if (minutes > 0) return tFormat('profile.minutesAgo', { n: minutes });
    return t('profile.justNow');
}

function formatCourseDuration(addedAt, completedAt) {
    if (!addedAt || !completedAt) return t('profile.unknown');
    const added = new Date(addedAt);
    const completed = new Date(completedAt);
    const diffMs = completed - added;
    const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (days > 0) return tFormat('profile.durationDays', { n: days });
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    if (hours > 0) return tFormat('profile.durationHours', { n: hours });
    return t('profile.durationLessThanHour');
}

function createStars() {
    const starsContainer = document.getElementById('stars');
    if (!starsContainer) return;
    for (let i = 0; i < 200; i++) {
        const star = document.createElement('div');
        star.classList.add('star');

        const x = Math.random() * window.innerWidth;
        const y = Math.random() * window.innerHeight;
        const size = Math.random() * 2 + 1;
        star.style.width = `${size}px`;
        star.style.height = `${size}px`;
        star.style.top = `${y}px`;
        star.style.left = `${x}px`;
        star.style.animationDuration = `${Math.random() * 3 + 2}s`;

        starsContainer.appendChild(star);
    }
}

const editModal = document.getElementById('editModal');
const closeModal = document.getElementById('closeModal');
const cancelEdit = document.getElementById('cancelEdit');

document.addEventListener('click', (e) => {
    const label = e.target && e.target.textContent ? e.target.textContent.trim() : '';
    if (editModal && (label === t('profile.editProfile') || label.includes('Edit Profile') || label.includes('Profili Düzenle'))) {
        editModal.classList.remove('hidden');
    }
});

if (closeModal && cancelEdit && editModal) {
    [closeModal, cancelEdit].forEach(el => {
        el.addEventListener('click', () => {
            editModal.classList.add('hidden');
        });
    });
}

window.addEventListener('DOMContentLoaded', () => {
    createStars();
});

function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    window.location.href = '/';
}

async function loadTournamentWins() {
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch('/api/user-tournament-wins', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            const container = document.getElementById('tournamentWinsContainer');
            const noWinsMessage = document.getElementById('noWinsMessage');

            if (data.tournament_wins && data.tournament_wins.length > 0) {
                noWinsMessage.style.display = 'none';

                container.innerHTML = '<div class="grid grid-cols-1 md:grid-cols-2 gap-3"></div>';
                const gridContainer = container.querySelector('.grid');

                data.tournament_wins.forEach((win) => {
                    const winCard = document.createElement('div');
                    winCard.className = 'bg-gradient-to-r from-yellow-500/10 to-orange-500/10 rounded-xl border border-yellow-500/20 p-4';

                    winCard.innerHTML = `
                        <div class="flex items-center space-x-3">
                            <div class="text-2xl">🏆</div>
                            <div class="flex-1 min-w-0">
                                <h4 class="text-sm font-semibold text-white truncate">${win.tournament_title}</h4>
                                <div class="flex items-center flex-wrap gap-x-3 text-xs text-gray-300 mt-1">
                                    <span class="text-green-400">${tFormat('profile.winCorrect', { correct: win.correct_answers, total: win.total_questions })}</span>
                                    <span class="text-blue-400">${tFormat('profile.winScore', { score: win.total_score })}</span>
                                    <span class="text-purple-400">${tFormat('profile.winParticipants', { count: win.total_participants })}</span>
                                </div>
                            </div>
                        </div>
                    `;

                    gridContainer.appendChild(winCard);
                });
            } else {
                noWinsMessage.style.display = 'block';
            }
        }
    } catch (error) {
        console.error('Turnuva kazanımları yüklenirken hata:', error);
    }
}

async function debugTournamentData() {
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch('/api/debug-tournament-data', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            console.log('DEBUG - Turnuva Verileri:', data);
        }
    } catch (error) {
        console.error('Debug verisi yüklenirken hata:', error);
    }
}

async function loadCompletedCourses() {
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch('/api/completed-courses', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            const activityContainer = document.getElementById('completedCoursesContainer');
            const noCompletedMessage = document.getElementById('noCompletedCoursesMessage');

            if (!activityContainer) return;

            if (data.completed_courses && data.completed_courses.length > 0) {
                if (noCompletedMessage) noCompletedMessage.style.display = 'none';
                activityContainer.innerHTML = '';

                data.completed_courses.forEach((course) => {
                    const activityItem = document.createElement('div');
                    activityItem.className = 'activity-item flex items-center space-x-4 p-4 rounded-xl';
                    const timeAgo = formatTimeAgo(course.completed_at);
                    const duration = formatCourseDuration(course.added_at, course.completed_at);

                    activityItem.innerHTML = `
                        <div class="w-10 h-10 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center">
                            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                            </svg>
                        </div>
                        <div class="flex-1">
                            <p class="text-white font-semibold">${tFormat('profile.courseCompleted', { title: course.title })}</p>
                            <p class="text-gray-400 text-sm">${tFormat('profile.courseMeta', { time: timeAgo, duration: duration })}</p>
                        </div>
                    `;

                    activityContainer.appendChild(activityItem);
                });

                if (data.completed_courses.length < 4) {
                    const remainingSlots = 4 - data.completed_courses.length;
                    const tournamentWinsResponse = await fetch('/api/user-tournament-wins', {
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (tournamentWinsResponse.ok) {
                        const winsData = await tournamentWinsResponse.json();
                        if (winsData.tournament_wins && winsData.tournament_wins.length > 0) {
                            winsData.tournament_wins.slice(0, remainingSlots).forEach((win) => {
                                const activityItem = document.createElement('div');
                                activityItem.className = 'activity-item flex items-center space-x-4 p-4 rounded-xl';

                                activityItem.innerHTML = `
                                    <div class="w-10 h-10 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full flex items-center justify-center">
                                        <span class="text-white text-lg">🏆</span>
                                    </div>
                                    <div class="flex-1">
                                        <p class="text-white font-semibold">${tFormat('profile.tournamentWon', { title: win.tournament_title })}</p>
                                        <p class="text-gray-400 text-sm">${tFormat('profile.tournamentWonScore', { score: win.total_score })}</p>
                                    </div>
                                `;

                                activityContainer.appendChild(activityItem);
                            });
                        }
                    }
                }
            } else if (noCompletedMessage) {
                noCompletedMessage.style.display = 'block';
            }
        }
    } catch (error) {
        console.error('Tamamlanan kurslar yüklenirken hata:', error);
    }
}

async function loadActiveCourse() {
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch('/api/active-course', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            const container = document.getElementById('activeCourseContainer');
            const noCourseMessage = document.getElementById('noActiveCourseMessage');

            if (data.active_course) {
                noCourseMessage.style.display = 'none';

                const course = data.active_course;
                const progressColor = course.progress_percentage >= 70 ? 'from-green-500 to-emerald-600' :
                                    course.progress_percentage >= 40 ? 'from-blue-500 to-purple-600' :
                                    'from-yellow-500 to-orange-600';

                const progressBgColor = course.progress_percentage >= 70 ? 'from-green-500/10 to-emerald-500/10' :
                                      course.progress_percentage >= 40 ? 'from-blue-500/10 to-purple-500/10' :
                                      'from-yellow-500/10 to-orange-500/10';

                const progressBorderColor = course.progress_percentage >= 70 ? 'border-green-500/20' :
                                          course.progress_percentage >= 40 ? 'border-blue-500/20' :
                                          'border-yellow-500/20';

                const progressTextColor = course.progress_percentage >= 70 ? 'text-green-300' :
                                        course.progress_percentage >= 40 ? 'text-blue-300' :
                                        'text-yellow-300';

                const progressBgTextColor = course.progress_percentage >= 70 ? 'bg-green-500/20' :
                                          course.progress_percentage >= 40 ? 'bg-blue-500/20' :
                                          'bg-yellow-500/20';

                container.innerHTML = `
                    <div class="bg-gradient-to-r ${progressBgColor} border ${progressBorderColor} rounded-2xl p-6 hover:scale-105 transition-transform duration-300">
                        <div class="flex items-center justify-between mb-4">
                            <div class="w-12 h-12 bg-gradient-to-r ${progressColor} rounded-xl flex items-center justify-center">
                                <span class="text-xl">📚</span>
                            </div>
                            <span class="text-xs ${progressBgTextColor} ${progressTextColor} px-2 py-1 rounded-full">${tFormat('profile.percentComplete', { percent: course.progress_percentage })}</span>
                        </div>
                        <h4 class="text-lg font-bold mb-2">${course.title}</h4>
                        <p class="text-gray-400 text-sm mb-4">${tFormat('profile.stepsCompleted', { completed: course.completed_steps, total: course.total_steps })}</p>
                        <div class="w-full bg-gray-700 rounded-full h-2 mb-4">
                            <div class="bg-gradient-to-r ${progressColor} h-2 rounded-full" style="width: ${course.progress_percentage}%"></div>
                        </div>
                        <button onclick="window.location.href='/roadmap'" class="text-blue-400 hover:text-blue-300 font-semibold text-sm transition-colors">${t('profile.continueBtn')}</button>
                    </div>
                `;
            } else {
                noCourseMessage.style.display = 'block';
            }
        }
    } catch (error) {
        console.error('Aktif kurs yüklenirken hata:', error);
    }
}
