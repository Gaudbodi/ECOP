interface AudioPlayerProps {
  src: string | undefined
  language: string
}

/**
 * AudioPlayer — minimal `<audio controls>` wrapper.
 *
 * Renders the per-language MP3 produced by enrichment_service.text_to_speech().
 * `preload="none"` avoids fetching every alert's audio on tab open — operators
 * may have many alerts in the list and auto-loading every MP3 is bandwidth-heavy.
 *
 * Phase 7 will add a HEAD-request existence check + "audio missing" badge
 * (REQ-pipeline-detail-audio-players); Phase 4 just renders the player or a
 * graceful empty-state when the URL is absent.
 */
export function AudioPlayer({ src, language }: AudioPlayerProps) {
  if (!src) {
    return (
      <div className="text-xs text-white/50 italic">
        No audio available for {language}
      </div>
    )
  }
  return (
    <audio
      controls
      preload="none"
      src={src}
      className="w-full max-w-md"
      aria-label={`${language} audio playback`}
    />
  )
}
