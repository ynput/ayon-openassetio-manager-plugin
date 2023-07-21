
"""
Trait definitions in the 'core' namespace.

Core traits.
"""

# WARNING: This file is auto-generated by openassetio-traitgen, do not edit.

from typing import Union

from openassetio import TraitsData


class ProductTrait:
    """
    A trait indicating the product of an entity in AYON.
    Usage: entity
    """
    kId = "Ayon:core.Product"

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

    
    def setProductId(self, productId: str):
        """
        Sets the productId property.

        Product ID of the entity.
        """
        if not isinstance(productId, str):
            raise TypeError("productId must be a 'str'.")
        self.__data.setTraitProperty(self.kId, "productId", productId)

    def getProductId(self, defaultValue: str=None) -> Union[str, None]:
        """
        Gets the value of the productId property or the supplied default.

        Product ID of the entity.
        """
        value = self.__data.getTraitProperty(self.kId, "productId")
        if value is None:
            return defaultValue

        if not isinstance(value, str):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'str'.")
            return defaultValue
        return value
        
    def setProductName(self, productName: str):
        """
        Sets the productName property.

        Product name of the entity.
        """
        if not isinstance(productName, str):
            raise TypeError("productName must be a 'str'.")
        self.__data.setTraitProperty(self.kId, "productName", productName)

    def getProductName(self, defaultValue: str=None) -> Union[str, None]:
        """
        Gets the value of the productName property or the supplied default.

        Product name of the entity.
        """
        value = self.__data.getTraitProperty(self.kId, "productName")
        if value is None:
            return defaultValue

        if not isinstance(value, str):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'str'.")
            return defaultValue
        return value
        
    


class RepresentationTrait:
    """
    A trait indicating the representation of an entity in AYON.
    Usage: entity
    """
    kId = "Ayon:core.Representation"

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

    
    def setFormat(self, format: str):
        """
        Sets the format property.

        Format of the files in representation.
        """
        if not isinstance(format, str):
            raise TypeError("format must be a 'str'.")
        self.__data.setTraitProperty(self.kId, "format", format)

    def getFormat(self, defaultValue: str=None) -> Union[str, None]:
        """
        Gets the value of the format property or the supplied default.

        Format of the files in representation.
        """
        value = self.__data.getTraitProperty(self.kId, "format")
        if value is None:
            return defaultValue

        if not isinstance(value, str):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'str'.")
            return defaultValue
        return value
        
    def setName(self, name: str):
        """
        Sets the name property.

        Name of the representation..
        """
        if not isinstance(name, str):
            raise TypeError("name must be a 'str'.")
        self.__data.setTraitProperty(self.kId, "name", name)

    def getName(self, defaultValue: str=None) -> Union[str, None]:
        """
        Gets the value of the name property or the supplied default.

        Name of the representation..
        """
        value = self.__data.getTraitProperty(self.kId, "name")
        if value is None:
            return defaultValue

        if not isinstance(value, str):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'str'.")
            return defaultValue
        return value
        
    def setTemplate(self, template: str):
        """
        Sets the template property.

        Template used to generate the files in representation.
        """
        if not isinstance(template, str):
            raise TypeError("template must be a 'str'.")
        self.__data.setTraitProperty(self.kId, "template", template)

    def getTemplate(self, defaultValue: str=None) -> Union[str, None]:
        """
        Gets the value of the template property or the supplied default.

        Template used to generate the files in representation.
        """
        value = self.__data.getTraitProperty(self.kId, "template")
        if value is None:
            return defaultValue

        if not isinstance(value, str):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'str'.")
            return defaultValue
        return value
        
    


class VersionTrait:
    """
    A trait indicating the version of an entity in AYON.
    Usage: entity
    """
    kId = "Ayon:core.Version"

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

    
    def setVersion(self, version: str):
        """
        Sets the version property.

        Version of the entity.
        """
        if not isinstance(version, str):
            raise TypeError("version must be a 'str'.")
        self.__data.setTraitProperty(self.kId, "version", version)

    def getVersion(self, defaultValue: str=None) -> Union[str, None]:
        """
        Gets the value of the version property or the supplied default.

        Version of the entity.
        """
        value = self.__data.getTraitProperty(self.kId, "version")
        if value is None:
            return defaultValue

        if not isinstance(value, str):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'str'.")
            return defaultValue
        return value
        
    def setVersionId(self, versionId: str):
        """
        Sets the versionId property.

        Version ID of the entity.
        """
        if not isinstance(versionId, str):
            raise TypeError("versionId must be a 'str'.")
        self.__data.setTraitProperty(self.kId, "versionId", versionId)

    def getVersionId(self, defaultValue: str=None) -> Union[str, None]:
        """
        Gets the value of the versionId property or the supplied default.

        Version ID of the entity.
        """
        value = self.__data.getTraitProperty(self.kId, "versionId")
        if value is None:
            return defaultValue

        if not isinstance(value, str):
            if defaultValue is None:
                raise TypeError(f"Invalid stored value type: '{type(value).__name__}' should be 'str'.")
            return defaultValue
        return value
        
    

