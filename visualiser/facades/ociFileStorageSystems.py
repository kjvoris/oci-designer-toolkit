#!/usr/bin/python
# Copyright (c) 2013, 2014-2019 Oracle and/or its affiliates. All rights reserved.


"""Provide Module Description
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
__author__ = ["Andrew Hopkinson (Oracle Cloud Solutions A-Team)"]
__copyright__ = "Copyright (c) 2013, 2014-2019  Oracle and/or its affiliates. All rights reserved."
__ekitversion__ = "@VERSION@"
__ekitrelease__ = "@RELEASE@"
__version__ = "1.0.0.0"
__date__ = "@BUILDDATE@"
__status__ = "@RELEASE@"
__module__ = "ociFileStorageSystems"
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


import oci

from common.ociLogging import getLogger
from facades.ociAvailabilityDomains import OCIAvailabilityDomains
from facades.ociConnection import OCIFileStorageSystemConnection

# Configure logging
logger = getLogger()


class OCIFileStorageSystems(OCIFileStorageSystemConnection):
    def __init__(self, config=None, configfile=None, compartment_id=None):
        self.compartment_id = compartment_id
        self.file_storage_systems_json = []
        self.file_storage_systems_obj = []
        super(OCIFileStorageSystems, self).__init__(config=config, configfile=configfile)

    def list(self, compartment_id=None, filter=None):
        if compartment_id is None:
            compartment_id = self.compartment_id

        # Add filter to only return AVAILABLE Compartments
        if filter is None:
            filter = {}

        if 'lifecycle_state' not in filter:
            filter['lifecycle_state'] = 'ACTIVE'

        oci_availability_domains = OCIAvailabilityDomains(config=self.config, compartment_id=compartment_id)
        file_storage_systems_json = []
        for oci_availability_domain in oci_availability_domains.list():
            logger.debug('Availability Domain {0!s:s}'.format(oci_availability_domain))
            file_storage_systems = oci.pagination.list_call_get_all_results(self.client.list_file_systems,
                                                                            compartment_id=compartment_id,
                                                                            availability_domain=oci_availability_domain['name']).data
            ad_file_storage_system_json = self.toJson(file_storage_systems)
            for file_storage_system in ad_file_storage_system_json:
                file_storage_system['availability_domain'] = list(oci_availability_domain['name'])[-1];
                exports = self.listExports(compartment_id, file_storage_system['id'])
                if len(exports) > 0:
                    file_storage_system['path'] = exports[0]['path']
                    file_storage_system['access'] = exports[0]['access']
                    file_storage_system['source'] = exports[0]['source']
                    mount_points = self.listMountTargets(compartment_id, oci_availability_domain['name'], exports[0]['export_set_id'])
                    if len(mount_points) > 0:
                        file_storage_system['subnet_id'] = mount_points[0]['subnet_id']
            # Convert to Json object
            file_storage_systems_json.extend(ad_file_storage_system_json)

        logger.debug('File Storage Systems {0!s:s}'.format(str(file_storage_systems_json)))

        # Filter results
        self.file_storage_systems_json = self.filterJsonObjectList(file_storage_systems_json, filter)
        logger.debug(str(self.file_storage_systems_json))

        return self.file_storage_systems_json

    def listExports(self, compartment_id, file_system_id):
        exports = oci.pagination.list_call_get_all_results(self.client.list_exports,
                                                            compartment_id=compartment_id,
                                                            file_system_id=file_system_id).data
        exports_json = self.toJson(exports)
        for export in exports_json:
            export_details = self.getExport(export['id'])
            logger.debug('Export Details {0!s:s}'.format(export_details))
            export['export_options'] = export_details['export_options']
            export['access'] = export_details['export_options'][0]['access']
            export['source'] = export_details['export_options'][0]['source']
        return exports_json

    def getExport(self, export_id):
        export = self.client.get_export(export_id=export_id).data
        return self.toJson(export)

    def listMountTargets(self, compartment_id, availability_domain, export_set_id):
        mount_targets = oci.pagination.list_call_get_all_results(self.client.list_mount_targets,
                                                                 compartment_id=compartment_id,
                                                                 availability_domain=availability_domain,
                                                                 export_set_id=export_set_id).data
        return self.toJson(mount_targets)

class OCIFileStorageSystem(object):
    def __init__(self, config=None, configfile=None, data=None):
        self.config = config
        self.configfile = configfile
        self.data = data
