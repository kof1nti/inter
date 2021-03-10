from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class Bufferb(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('individualpostcodes', 'Individual Postcodes', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('postcodes', 'Postcodes', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('MilesNearestNeighbours', '3 miles nearest neighbours', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(5, model_feedback)
        results = {}
        outputs = {}

        # Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 4828.03,
            'END_CAP_STYLE': 0,
            'INPUT': parameters['individualpostcodes'],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Clip
        alg_params = {
            'INPUT': parameters['postcodes'],
            'OVERLAY': outputs['Buffer']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Clip'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Convert multipoints to points
        alg_params = {
            'MULTIPOINTS': outputs['Clip']['OUTPUT'],
            'POINTS': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ConvertMultipointsToPoints'] = processing.run('saga:convertmultipointstopoints', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Distance matrix
        alg_params = {
            'INPUT': parameters['individualpostcodes'],
            'INPUT_FIELD': 'field_1_1',
            'MATRIX_TYPE': 0,
            'NEAREST_POINTS': 0,
            'TARGET': outputs['ConvertMultipointsToPoints']['POINTS'],
            'TARGET_FIELD': 'field_1_1',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DistanceMatrix'] = processing.run('qgis:distancematrix', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Drop field(s)
        alg_params = {
            'COLUMN': 'Distance',
            'INPUT': outputs['DistanceMatrix']['OUTPUT'],
            'OUTPUT': parameters['MilesNearestNeighbours']
        }
        outputs['DropFields'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['MilesNearestNeighbours'] = outputs['DropFields']['OUTPUT']
        return results

    def name(self):
        return 'bufferb'

    def displayName(self):
        return 'bufferb'

    def group(self):
        return 'Nearest neighbours'

    def groupId(self):
        return 'Nearest neighbours'

    def createInstance(self):
        return Bufferb()
