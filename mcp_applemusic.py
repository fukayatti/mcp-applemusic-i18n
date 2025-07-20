import subprocess
import re
from mcp.server.fastmcp import FastMCP


def sanitize_query(query: str) -> str:
    """Sanitize query string to prevent AppleScript injection."""
    # Remove or escape potentially dangerous characters
    query = query.replace('"', '\\"')
    query = query.replace("'", "\\'")
    query = re.sub(r'[^\w\s\-\.\(\)&]', '', query)
    return query[:100]  # Limit length


def run_applescript(script: str) -> str:
    """Execute an AppleScript command via osascript and return its output."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script], 
            capture_output=True, 
            text=True, 
            timeout=30  # 30秒のタイムアウトを追加
        )
        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Error: AppleScript execution timed out"
    except Exception as e:
        return f"Error: {str(e)}"


# Instantiate the MCP server.
mcp = FastMCP("iTunesControlServer")


@mcp.tool()
def itunes_play() -> str:
    """Start playback in Music (iTunes)."""
    script = 'tell application "Music" to play'
    return run_applescript(script)


@mcp.tool()
def itunes_pause() -> str:
    """Pause playback in Music (iTunes)."""
    script = 'tell application "Music" to pause'
    return run_applescript(script)


@mcp.tool()
def itunes_next() -> str:
    """Skip to the next track."""
    script = 'tell application "Music" to next track'
    return run_applescript(script)


@mcp.tool()
def itunes_previous() -> str:
    """Return to the previous track."""
    script = 'tell application "Music" to previous track'
    return run_applescript(script)


@mcp.tool()
def itunes_search(query: str) -> str:
    """
    Search the Music library for tracks whose names contain the given query.
    Returns a list of tracks formatted as "Track Name - Artist".
    """
    sanitized_query = sanitize_query(query)
    script = f"""
    tell application "Music"
        set trackList to every track whose name contains "{sanitized_query}"
        set output to ""
        repeat with t in trackList
            set output to output & (name of t) & " - " & (artist of t) & linefeed
        end repeat
        return output
    end tell
    """
    return run_applescript(script)


@mcp.tool()
def itunes_play_song(song: str) -> str:
    """
    Play the first track whose name exactly matches the given song name.
    Returns a confirmation message.
    """
    sanitized_song = sanitize_query(song)
    script = f"""
    tell application "Music"
        set theTrack to first track whose name is "{sanitized_song}"
        play theTrack
        return "Now playing: " & (name of theTrack) & " by " & (artist of theTrack)
    end tell
    """
    return run_applescript(script)


@mcp.tool()
def itunes_create_playlist(name: str, songs: str) -> str:
    """
    Create a new playlist with the given name and add tracks to it.
    'songs' should be a comma-separated list of exact track names.
    Returns a confirmation message including the number of tracks added.
    """
    # Split the songs string into a list.
    song_list = [sanitize_query(s.strip()) for s in songs.split(",") if s.strip()]
    if not song_list:
        return "No songs provided."
    # Build a condition string that matches any one of the song names.
    # Example: 'name is "Song1" or name is "Song2"'
    conditions = " or ".join([f'name is "{s}"' for s in song_list])
    sanitized_name = sanitize_query(name)
    script = f"""
    tell application "Music"
        set newPlaylist to make new user playlist with properties {{name:"{sanitized_name}"}}
        set matchingTracks to every track whose ({conditions})
        repeat with t in matchingTracks
            duplicate t to newPlaylist
        end repeat
        return "Playlist \\"{sanitized_name}\\" created with " & (count of tracks of newPlaylist) & " tracks."
    end tell
    """
    return run_applescript(script)


@mcp.tool()
def itunes_library() -> str:
    """
    Return a summary of the Music library, including total tracks and user playlists.
    """
    script = """
    tell application "Music"
        set totalTracks to count of every track
        set totalPlaylists to count of user playlists
        return "Total tracks: " & totalTracks & linefeed & "Total playlists: " & totalPlaylists
    end tell
    """
    return run_applescript(script)


@mcp.tool()
def itunes_current_song() -> str:
    """
    Get information about the currently playing track.
    Returns the track name, artist, and album.
    """
    script = """
    tell application "Music"
        if player state is playing then
            set currentTrack to current track
            return "Now playing: " & (name of currentTrack) & " by " & (artist of currentTrack) & " from " & (album of currentTrack)
        else
            return "No track is currently playing"
        end if
    end tell
    """
    return run_applescript(script)


@mcp.tool()
def itunes_all_songs() -> str:
    """
    Get a list of all songs in the Music library.
    Returns a formatted list of all tracks with their names and artists.
    Note: This may take a while for large libraries and is limited to first 100 tracks.
    """
    script = """
    tell application "Music"
        set trackList to tracks 1 thru 100
        set output to ""
        repeat with t in trackList
            set output to output & (name of t) & " - " & (artist of t) & linefeed
        end repeat
        return output
    end tell
    """
    return run_applescript(script)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
