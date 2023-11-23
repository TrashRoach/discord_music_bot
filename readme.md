```python
from dataclasses import dataclass
from enum import Enum, auto

from past import OldProject


class ProjectState(Enum):
    COMPLETED: auto()
    WIP = auto()
    TODO = auto()
    FUTURE = auto()

    def description(self):
        if self == ProjectState.COMPLETED:
            return 'All done. Small refactoring is possible.'
        elif self == ProjectState.WIP:
            return 'Work in progress. Some changes may occur.'
        elif self == ProjectState.TODO:
            return 'Not implemented yet or backlogged.'
        elif self == ProjectState.FUTURE:
            return 'SOON™'


@dataclass
class NewProject(OldProject):
    player_core: ProjectState = ProjectState.COMPLETED  # ITS ALIVE!
    youtube_source: ProjectState = ProjectState.COMPLETED  # music from YouTube
    
    commands: ProjectState = ProjectState.WIP  # Cog commands to hybrid_commands
    control_view: ProjectState = ProjectState.WIP  # MusicPlayerView
    
    logging: ProjectState = ProjectState.TODO  #  Error Handling mostly
    testing: ProjectState = ProjectState.TODO  #  Please, for the love of God...
    CI_CD: ProjectState = ProjectState.TODO  #  Lint, auto testing, deploy, etc...
    docker: ProjectState = ProjectState.TODO  #  'Cause its neat
    cleanup: ProjectState = ProjectState.TODO  #  I might need some old stuff
    readme: ProjectState = ProjectState.TODO  #  ...yeah
    
    more_sources: ProjectState = ProjectState.FUTURE  #  Spotify, etc
    optimisation: ProjectState = ProjectState.FUTURE  #  If it ain't broke, don't fix it :^)
```