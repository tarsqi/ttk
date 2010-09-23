
from library.tarsqi_constants import PREPROCESSOR, GUTIME, EVITA, SLINKET
from library.tarsqi_constants import S2T, CLASSIFIER, BLINKER, LINK_MERGER, ARGLINKER

from preprocessing.wrapper import PreprocessorWrapper
from gutime.wrapper import GUTimeWrapper
from evita.wrapper import EvitaWrapper
from slinket.wrapper import SlinketWrapper
from s2t.wrapper import S2tWrapper
from blinker.wrapper import BlinkerWrapper
from classifier.wrapper import ClassifierWrapper
from merging.wrapper import MergerWrapper
from arglinker.wrapper import ArgLinkerWrapper

COMPONENTS = {
    PREPROCESSOR: PreprocessorWrapper,
    GUTIME: GUTimeWrapper,
    EVITA: EvitaWrapper,
    SLINKET: SlinketWrapper,
    S2T: S2tWrapper,
    BLINKER: BlinkerWrapper,
    CLASSIFIER: ClassifierWrapper,
    LINK_MERGER: MergerWrapper,
    ARGLINKER: ArgLinkerWrapper }
