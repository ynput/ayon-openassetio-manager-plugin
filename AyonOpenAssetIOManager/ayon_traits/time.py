
"""
Trait definitions in the 'time' namespace.

Traits related to time.
"""

# WARNING: This file is auto-generated by openassetio-traitgen, do not edit.

from typing import Union

from openassetio import TraitsData


class AnimationTrait:
    """
    A trait indicating an animation.
    Usage: entity
    """
    kId = "Ayon:time.Animation"

    def __init__(self, traitsData):
        """
        Construct this trait view, wrapping the given data.

        @param traitsData @fqref{TraitsData}} "TraitsData" The target
        data that holds/will hold the traits properties.
        """
        self.__data = traitsData

    def isImbued(self):
        """
        Checks whether the data this trait has been applied to
        actually has this trait.
        @return `True` if the underlying data has this trait, `False`
        otherwise.
        """
        return self.isImbuedTo(self.__data)

    @classmethod
    def isImbuedTo(cls, traitsData):
        """
        Checks whether the given data actually has this trait.
        @param traitsData: Data to check for trait.
        @return `True` if the underlying data has this trait, `False`
        otherwise.
        """
        return traitsData.hasTrait(cls.kId)

    def imbue(self):
        """
        Adds this trait to the held data.

        If the data already has this trait, it is a no-op.
        """
        self.__data.addTrait(self.kId)

    @classmethod
    def imbueTo(cls, traitsData):
        """
        Adds this trait to the provided data.

        If the data already has this trait, it is a no-op.
        """
        traitsData.addTrait(cls.kId)

    
    def setLoop(self, loop: bool):
        """
        Sets the loop property.

        Indicate if animation is looped.
        """
        if not isinstance(loop, bool):
            raise TypeError("loop must be a 'bool'.")
        self.__data.setTraitProperty(self.kId, "loop", loop)

    def getLoop(self, defaultValue: bool=None) -> Union[bool, None]:
        """
        Gets the value of the loop property or the supplied default.

        Indicate if animation is looped.
        """
        value = self.__data.getTraitProperty(self.kId, "loop")
        if value is None:
            return defaultValue

        if not isinstance(value, bool):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'bool'.")
            return defaultValue
        return value
        
    


class CacheTrait:
    """
    A trait indicating a cached entity.
    Usage: entity
    """
    kId = "Ayon:time.Cache"

    def __init__(self, traitsData):
        """
        Construct this trait view, wrapping the given data.

        @param traitsData @fqref{TraitsData}} "TraitsData" The target
        data that holds/will hold the traits properties.
        """
        self.__data = traitsData

    def isImbued(self):
        """
        Checks whether the data this trait has been applied to
        actually has this trait.
        @return `True` if the underlying data has this trait, `False`
        otherwise.
        """
        return self.isImbuedTo(self.__data)

    @classmethod
    def isImbuedTo(cls, traitsData):
        """
        Checks whether the given data actually has this trait.
        @param traitsData: Data to check for trait.
        @return `True` if the underlying data has this trait, `False`
        otherwise.
        """
        return traitsData.hasTrait(cls.kId)

    def imbue(self):
        """
        Adds this trait to the held data.

        If the data already has this trait, it is a no-op.
        """
        self.__data.addTrait(self.kId)

    @classmethod
    def imbueTo(cls, traitsData):
        """
        Adds this trait to the provided data.

        If the data already has this trait, it is a no-op.
        """
        traitsData.addTrait(cls.kId)

    


class ClipTrait:
    """
    A trait indicating time defined clip with start, end and rate.
    Usage: entity
    """
    kId = "Ayon:time.Clip"

    def __init__(self, traitsData):
        """
        Construct this trait view, wrapping the given data.

        @param traitsData @fqref{TraitsData}} "TraitsData" The target
        data that holds/will hold the traits properties.
        """
        self.__data = traitsData

    def isImbued(self):
        """
        Checks whether the data this trait has been applied to
        actually has this trait.
        @return `True` if the underlying data has this trait, `False`
        otherwise.
        """
        return self.isImbuedTo(self.__data)

    @classmethod
    def isImbuedTo(cls, traitsData):
        """
        Checks whether the given data actually has this trait.
        @param traitsData: Data to check for trait.
        @return `True` if the underlying data has this trait, `False`
        otherwise.
        """
        return traitsData.hasTrait(cls.kId)

    def imbue(self):
        """
        Adds this trait to the held data.

        If the data already has this trait, it is a no-op.
        """
        self.__data.addTrait(self.kId)

    @classmethod
    def imbueTo(cls, traitsData):
        """
        Adds this trait to the provided data.

        If the data already has this trait, it is a no-op.
        """
        traitsData.addTrait(cls.kId)

    
    def setClipIn(self, clipIn: int):
        """
        Sets the clipIn property.

        Frame number where the clip starts in the parent clip.
        """
        if not isinstance(clipIn, int):
            raise TypeError("clipIn must be a 'int'.")
        self.__data.setTraitProperty(self.kId, "clipIn", clipIn)

    def getClipIn(self, defaultValue: int=None) -> Union[int, None]:
        """
        Gets the value of the clipIn property or the supplied default.

        Frame number where the clip starts in the parent clip.
        """
        value = self.__data.getTraitProperty(self.kId, "clipIn")
        if value is None:
            return defaultValue

        if not isinstance(value, int):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'int'.")
            return defaultValue
        return value
        
    def setClipOut(self, clipOut: int):
        """
        Sets the clipOut property.

        Frame number where the clip ends in the parent clip.
        """
        if not isinstance(clipOut, int):
            raise TypeError("clipOut must be a 'int'.")
        self.__data.setTraitProperty(self.kId, "clipOut", clipOut)

    def getClipOut(self, defaultValue: int=None) -> Union[int, None]:
        """
        Gets the value of the clipOut property or the supplied default.

        Frame number where the clip ends in the parent clip.
        """
        value = self.__data.getTraitProperty(self.kId, "clipOut")
        if value is None:
            return defaultValue

        if not isinstance(value, int):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'int'.")
            return defaultValue
        return value
        
    def setFrameEnd(self, frameEnd: int):
        """
        Sets the frameEnd property.

        Frame number where the clip ends.
        """
        if not isinstance(frameEnd, int):
            raise TypeError("frameEnd must be a 'int'.")
        self.__data.setTraitProperty(self.kId, "frameEnd", frameEnd)

    def getFrameEnd(self, defaultValue: int=None) -> Union[int, None]:
        """
        Gets the value of the frameEnd property or the supplied default.

        Frame number where the clip ends.
        """
        value = self.__data.getTraitProperty(self.kId, "frameEnd")
        if value is None:
            return defaultValue

        if not isinstance(value, int):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'int'.")
            return defaultValue
        return value
        
    def setFrameRate(self, frameRate: float):
        """
        Sets the frameRate property.

        Frame rate of the clip.
        """
        if not isinstance(frameRate, float):
            raise TypeError("frameRate must be a 'float'.")
        self.__data.setTraitProperty(self.kId, "frameRate", frameRate)

    def getFrameRate(self, defaultValue: float=None) -> Union[float, None]:
        """
        Gets the value of the frameRate property or the supplied default.

        Frame rate of the clip.
        """
        value = self.__data.getTraitProperty(self.kId, "frameRate")
        if value is None:
            return defaultValue

        if not isinstance(value, float):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'float'.")
            return defaultValue
        return value
        
    def setFrameStart(self, frameStart: int):
        """
        Sets the frameStart property.

        Frame number where the clip starts.
        """
        if not isinstance(frameStart, int):
            raise TypeError("frameStart must be a 'int'.")
        self.__data.setTraitProperty(self.kId, "frameStart", frameStart)

    def getFrameStart(self, defaultValue: int=None) -> Union[int, None]:
        """
        Gets the value of the frameStart property or the supplied default.

        Frame number where the clip starts.
        """
        value = self.__data.getTraitProperty(self.kId, "frameStart")
        if value is None:
            return defaultValue

        if not isinstance(value, int):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'int'.")
            return defaultValue
        return value
        
    def setHandlesEnd(self, handlesEnd: int):
        """
        Sets the handlesEnd property.

        Number of frames of handles at the end of the clip.
        """
        if not isinstance(handlesEnd, int):
            raise TypeError("handlesEnd must be a 'int'.")
        self.__data.setTraitProperty(self.kId, "handlesEnd", handlesEnd)

    def getHandlesEnd(self, defaultValue: int=None) -> Union[int, None]:
        """
        Gets the value of the handlesEnd property or the supplied default.

        Number of frames of handles at the end of the clip.
        """
        value = self.__data.getTraitProperty(self.kId, "handlesEnd")
        if value is None:
            return defaultValue

        if not isinstance(value, int):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'int'.")
            return defaultValue
        return value
        
    def setHandlesStart(self, handlesStart: int):
        """
        Sets the handlesStart property.

        Number of frames of handles at the start of the clip.
        """
        if not isinstance(handlesStart, int):
            raise TypeError("handlesStart must be a 'int'.")
        self.__data.setTraitProperty(self.kId, "handlesStart", handlesStart)

    def getHandlesStart(self, defaultValue: int=None) -> Union[int, None]:
        """
        Gets the value of the handlesStart property or the supplied default.

        Number of frames of handles at the start of the clip.
        """
        value = self.__data.getTraitProperty(self.kId, "handlesStart")
        if value is None:
            return defaultValue

        if not isinstance(value, int):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'int'.")
            return defaultValue
        return value
        
    def setInclusiveHandles(self, inclusiveHandles: bool):
        """
        Sets the inclusiveHandles property.

        Whether the handles are included in the clip.
        """
        if not isinstance(inclusiveHandles, bool):
            raise TypeError("inclusiveHandles must be a 'bool'.")
        self.__data.setTraitProperty(self.kId, "inclusiveHandles", inclusiveHandles)

    def getInclusiveHandles(self, defaultValue: bool=None) -> Union[bool, None]:
        """
        Gets the value of the inclusiveHandles property or the supplied default.

        Whether the handles are included in the clip.
        """
        value = self.__data.getTraitProperty(self.kId, "inclusiveHandles")
        if value is None:
            return defaultValue

        if not isinstance(value, bool):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'bool'.")
            return defaultValue
        return value
        
    def setStep(self, step: int):
        """
        Sets the step property.

        Frame step of the clip.
        """
        if not isinstance(step, int):
            raise TypeError("step must be a 'int'.")
        self.__data.setTraitProperty(self.kId, "step", step)

    def getStep(self, defaultValue: int=None) -> Union[int, None]:
        """
        Gets the value of the step property or the supplied default.

        Frame step of the clip.
        """
        value = self.__data.getTraitProperty(self.kId, "step")
        if value is None:
            return defaultValue

        if not isinstance(value, int):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'int'.")
            return defaultValue
        return value
        
    def setTimecode(self, timecode: str):
        """
        Sets the timecode property.

        Timecode of the clip.
        """
        if not isinstance(timecode, str):
            raise TypeError("timecode must be a 'str'.")
        self.__data.setTraitProperty(self.kId, "timecode", timecode)

    def getTimecode(self, defaultValue: str=None) -> Union[str, None]:
        """
        Gets the value of the timecode property or the supplied default.

        Timecode of the clip.
        """
        value = self.__data.getTraitProperty(self.kId, "timecode")
        if value is None:
            return defaultValue

        if not isinstance(value, str):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'str'.")
            return defaultValue
        return value
        
    


class SequenceTrait:
    """
    A trait similar to Clip.
    Usage: entity
    """
    kId = "Ayon:time.Sequence"

    def __init__(self, traitsData):
        """
        Construct this trait view, wrapping the given data.

        @param traitsData @fqref{TraitsData}} "TraitsData" The target
        data that holds/will hold the traits properties.
        """
        self.__data = traitsData

    def isImbued(self):
        """
        Checks whether the data this trait has been applied to
        actually has this trait.
        @return `True` if the underlying data has this trait, `False`
        otherwise.
        """
        return self.isImbuedTo(self.__data)

    @classmethod
    def isImbuedTo(cls, traitsData):
        """
        Checks whether the given data actually has this trait.
        @param traitsData: Data to check for trait.
        @return `True` if the underlying data has this trait, `False`
        otherwise.
        """
        return traitsData.hasTrait(cls.kId)

    def imbue(self):
        """
        Adds this trait to the held data.

        If the data already has this trait, it is a no-op.
        """
        self.__data.addTrait(self.kId)

    @classmethod
    def imbueTo(cls, traitsData):
        """
        Adds this trait to the provided data.

        If the data already has this trait, it is a no-op.
        """
        traitsData.addTrait(cls.kId)

    
    def setAllowGaps(self, allowGaps: bool):
        """
        Sets the allowGaps property.

        Whether the sequence allows gaps.
        """
        if not isinstance(allowGaps, bool):
            raise TypeError("allowGaps must be a 'bool'.")
        self.__data.setTraitProperty(self.kId, "allowGaps", allowGaps)

    def getAllowGaps(self, defaultValue: bool=None) -> Union[bool, None]:
        """
        Gets the value of the allowGaps property or the supplied default.

        Whether the sequence allows gaps.
        """
        value = self.__data.getTraitProperty(self.kId, "allowGaps")
        if value is None:
            return defaultValue

        if not isinstance(value, bool):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'bool'.")
            return defaultValue
        return value
        
    

