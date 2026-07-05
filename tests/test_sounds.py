def test_sound_enum_values():
    from voice_assistant.audio.sounds import Sound

    assert Sound.READY_TO_LISTEN.value == 1
    assert Sound.SEARCH_STARTED.value == 2
    assert Sound.STARTUP.value == 3
    assert Sound.DONE.value == 4


def test_make_sound_not_loaded(mock_make_sound):
    from voice_assistant.audio import sounds as sounds_mod

    sounds_mod._sounds.clear()
    sounds_mod.make_sound(sounds_mod.Sound.READY_TO_LISTEN)


def test_with_sound_effects_decorator(mock_make_sound, mock_speak):
    from voice_assistant.audio.sounds import with_sound_effects

    @with_sound_effects(say_done=True)
    def my_action():
        mock_speak("hello")

    my_action()

    assert mock_make_sound.call_count == 2
    assert mock_speak.call_count == 2


def test_with_sound_effects_no_done(mock_make_sound, mock_speak):
    from voice_assistant.audio.sounds import with_sound_effects

    @with_sound_effects(say_done=False)
    def my_action():
        pass

    my_action()

    assert mock_make_sound.call_count == 2
    assert mock_speak.call_count == 0
