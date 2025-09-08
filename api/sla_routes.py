from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from datetime import datetime, timedelta
from typing import Optional

from .dependencies import verify_token, init_session
from .models import (SLAMetrics, IncidentTracking, PerformanceMetrics,
                    EndPoints, EndPointsData, Alerts)



sla_router = APIRouter(prefix="/sla", tags=["sla"], dependencies=[Depends(verify_token)])


@sla_router.get("/summary")
async def get_sla_summary(
    days: int = Query(30, description="Número de dias para análise"),
    session: Session = Depends(init_session)
):
    """
    Retorna dados brutos de SLA dos últimos N dias para processamento no frontend.
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Buscar dados básicos dos endpoints
        endpoints = session.query(EndPoints).all()
        
        # Buscar métricas SLA
        sla_metrics = session.query(SLAMetrics).filter(
            SLAMetrics.timestamp >= cutoff_date
        ).all()
        
        # Buscar incidentes
        incidents = session.query(IncidentTracking).filter(
            IncidentTracking.start_time >= cutoff_date
        ).all()
        
        # Buscar dados de performance
        performance_data = session.query(EndPointsData).filter(
            EndPointsData.last_updated >= cutoff_date
        ).order_by(EndPointsData.last_updated.desc()).all()
        
        # Buscar alertas
        alerts = session.query(Alerts).filter(
            Alerts.created_at >= cutoff_date
        ).all()
        
        return {
            "status": "success",
            "data": {
                "endpoints": [
                    {
                        "id": ep.id,
                        "ip": ep.ip,
                        "nickname": ep.nickname,
                        "interval": ep.interval
                    } for ep in endpoints
                ],
                "sla_metrics": [
                    {
                        "id": sla.id,
                        "endpoint_id": sla.endpoint_id,
                        "timestamp": sla.timestamp.isoformat(),
                        "availability_percentage": sla.availability_percentage,
                        "uptime_seconds": sla.uptime_seconds,
                        "downtime_seconds": sla.downtime_seconds,
                        "mttr_minutes": sla.mttr_minutes,
                        "incidents_count": sla.incidents_count,
                        "sla_target": sla.sla_target,
                        "sla_compliance": sla.sla_compliance,
                        "avg_response_time": sla.avg_response_time
                    } for sla in sla_metrics
                ],
                "incidents": [
                    {
                        "id": inc.id,
                        "endpoint_id": inc.endpoint_id,
                        "incident_type": inc.incident_type,
                        "severity": inc.severity,
                        "status": inc.status,
                        "start_time": inc.start_time.isoformat(),
                        "end_time": inc.end_time.isoformat() if inc.end_time else None,
                        "duration_seconds": inc.duration_seconds,
                        "resolution_time_minutes": inc.resolution_time_minutes,
                        "impact_description": inc.impact_description
                    } for inc in incidents
                ],
                "performance_data": [
                    {
                        "id": pd.id,
                        "endpoint_id": pd.id_end_point,
                        "timestamp": pd.last_updated.isoformat(),
                        "status": pd.status,
                        "ping_rtt": pd.ping_rtt,
                        "snmp_rtt": pd.snmp_rtt,
                        "cpu_load": pd.hrProcessorLoad,
                        "memory_total": pd.memTotalReal,
                        "memory_avail": pd.memAvailReal
                    } for pd in performance_data
                ],
                "alerts": [
                    {
                        "id": alert.id,
                        "endpoint_id": alert.id_endpoint,
                        "title": alert.title,
                        "severity": alert.severity,
                        "category": alert.category,
                        "status": alert.status,
                        "created_at": alert.created_at.isoformat(),
                        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
                    } for alert in alerts
                ],
                "summary": {
                    "period_days": days,
                    "total_endpoints": len(endpoints),
                    "total_incidents": len(incidents),
                    "total_alerts": len(alerts),
                    "analysis_start_date": cutoff_date.isoformat(),
                    "analysis_end_date": datetime.now().isoformat()
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados de SLA: {str(e)}")
    finally:
        session.close()


@sla_router.get("/endpoint/{endpoint_id}")
async def get_endpoint_sla_details(
    endpoint_id: int,
    days: int = Query(30, description="Número de dias para análise"),
    session: Session = Depends(init_session)
):
    """
    Retorna dados detalhados de SLA para um endpoint específico.
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Verificar se endpoint existe
        endpoint = session.query(EndPoints).filter(EndPoints.id == endpoint_id).first()
        if not endpoint:
            raise HTTPException(status_code=404, detail="Endpoint não encontrado")
        
        # Buscar métricas SLA específicas
        sla_metrics = session.query(SLAMetrics).filter(
            and_(
                SLAMetrics.endpoint_id == endpoint_id,
                SLAMetrics.timestamp >= cutoff_date
            )
        ).order_by(SLAMetrics.timestamp.desc()).all()
        
        # Buscar incidentes específicos
        incidents = session.query(IncidentTracking).filter(
            and_(
                IncidentTracking.endpoint_id == endpoint_id,
                IncidentTracking.start_time >= cutoff_date
            )
        ).order_by(IncidentTracking.start_time.desc()).all()
        
        # Buscar métricas de performance específicas
        performance_metrics = session.query(PerformanceMetrics).filter(
            and_(
                PerformanceMetrics.endpoint_id == endpoint_id,
                PerformanceMetrics.timestamp >= cutoff_date
            )
        ).order_by(PerformanceMetrics.timestamp.desc()).all()
        
        # Buscar dados brutos de monitoramento
        raw_data = session.query(EndPointsData).filter(
            and_(
                EndPointsData.id_end_point == endpoint_id,
                EndPointsData.last_updated >= cutoff_date
            )
        ).order_by(EndPointsData.last_updated.desc()).limit(1000).all()
        
        return {
            "status": "success",
            "data": {
                "endpoint": {
                    "id": endpoint.id,
                    "ip": endpoint.ip,
                    "nickname": endpoint.nickname,
                    "interval": endpoint.interval
                },
                "sla_metrics": [
                    {
                        "timestamp": sla.timestamp.isoformat(),
                        "availability_percentage": sla.availability_percentage,
                        "uptime_seconds": sla.uptime_seconds,
                        "downtime_seconds": sla.downtime_seconds,
                        "mttr_minutes": sla.mttr_minutes,
                        "mtbf_hours": sla.mtbf_hours,
                        "incidents_count": sla.incidents_count,
                        "sla_compliance": sla.sla_compliance,
                        "avg_response_time": sla.avg_response_time,
                        "max_response_time": sla.max_response_time,
                        "min_response_time": sla.min_response_time
                    } for sla in sla_metrics
                ],
                "incidents": [
                    {
                        "id": inc.id,
                        "incident_type": inc.incident_type,
                        "severity": inc.severity,
                        "status": inc.status,
                        "start_time": inc.start_time.isoformat(),
                        "end_time": inc.end_time.isoformat() if inc.end_time else None,
                        "duration_seconds": inc.duration_seconds,
                        "resolution_time_minutes": inc.resolution_time_minutes,
                        "impact_description": inc.impact_description,
                        "resolution_notes": inc.resolution_notes
                    } for inc in incidents
                ],
                "performance_metrics": [
                    {
                        "timestamp": pm.timestamp.isoformat(),
                        "response_time_p50": pm.response_time_p50,
                        "response_time_p90": pm.response_time_p90,
                        "response_time_p95": pm.response_time_p95,
                        "response_time_p99": pm.response_time_p99,
                        "response_time_avg": pm.response_time_avg,
                        "error_rate_percentage": pm.error_rate_percentage,
                        "total_requests": pm.total_requests,
                        "sample_count": pm.sample_count
                    } for pm in performance_metrics
                ],
                "raw_monitoring_data": [
                    {
                        "timestamp": rd.last_updated.isoformat(),
                        "status": rd.status,
                        "ping_rtt": rd.ping_rtt,
                        "snmp_rtt": rd.snmp_rtt
                    } for rd in raw_data
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar detalhes de SLA: {str(e)}")
    finally:
        session.close()


@sla_router.get("/compliance")
async def get_sla_compliance_report(
    session: Session = Depends(init_session)
):
    """
    Retorna relatório de compliance de SLA de todos os endpoints.
    """
    try:
        # Buscar últimas métricas de cada endpoint
        latest_sla = session.query(
            SLAMetrics.endpoint_id,
            func.max(SLAMetrics.timestamp).label('latest_timestamp')
        ).group_by(SLAMetrics.endpoint_id).subquery()
        
        current_sla_metrics = session.query(SLAMetrics).join(
            latest_sla,
            and_(
                SLAMetrics.endpoint_id == latest_sla.c.endpoint_id,
                SLAMetrics.timestamp == latest_sla.c.latest_timestamp
            )
        ).all()
        
        # Buscar informações dos endpoints
        endpoints = session.query(EndPoints).all()
        endpoint_dict = {ep.id: ep for ep in endpoints}
        
        compliance_data = []
        total_endpoints = 0
        compliant_endpoints = 0
        
        for sla in current_sla_metrics:
            endpoint = endpoint_dict.get(sla.endpoint_id)
            if endpoint:
                total_endpoints += 1
                if sla.sla_compliance:
                    compliant_endpoints += 1
                    
                compliance_data.append({
                    "endpoint_id": sla.endpoint_id,
                    "endpoint_ip": endpoint.ip,
                    "endpoint_name": endpoint.nickname or endpoint.ip,
                    "availability_percentage": sla.availability_percentage,
                    "sla_target": sla.sla_target,
                    "sla_compliance": sla.sla_compliance,
                    "mttr_minutes": sla.mttr_minutes,
                    "incidents_count": sla.incidents_count,
                    "last_measurement": sla.timestamp.isoformat()
                })
        
        overall_compliance = (compliant_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0
        
        return {
            "status": "success",
            "data": {
                "overall_compliance_percentage": round(overall_compliance, 2),
                "total_endpoints": total_endpoints,
                "compliant_endpoints": compliant_endpoints,
                "non_compliant_endpoints": total_endpoints - compliant_endpoints,
                "endpoints": compliance_data
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório de compliance: {str(e)}")
    finally:
        session.close()


@sla_router.get("/incidents/summary")
async def get_incidents_summary(
    days: int = Query(30, description="Número de dias para análise"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    severity: Optional[str] = Query(None, description="Filtrar por severidade"),
    session: Session = Depends(init_session),
    current_user = Depends(verify_token)
):
    """
    Retorna resumo de incidentes para análise.
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Construir query base
        query = session.query(IncidentTracking).filter(
            IncidentTracking.start_time >= cutoff_date
        )
        
        # Aplicar filtros opcionais
        if status:
            query = query.filter(IncidentTracking.status == status)
        if severity:
            query = query.filter(IncidentTracking.severity == severity)
            
        incidents = query.order_by(IncidentTracking.start_time.desc()).all()
        
        # Estatísticas
        total_incidents = len(incidents)
        open_incidents = len([i for i in incidents if i.status == "open"])
        resolved_incidents = len([i for i in incidents if i.status == "resolved"])
        
        # MTTR médio
        resolved_with_time = [i for i in incidents if i.resolution_time_minutes is not None]
        avg_mttr = sum(i.resolution_time_minutes for i in resolved_with_time) / len(resolved_with_time) if resolved_with_time else 0
        
        # Incidentes por severidade
        severity_counts = {}
        for incident in incidents:
            severity_counts[incident.severity] = severity_counts.get(incident.severity, 0) + 1
        
        # Incidentes por tipo
        type_counts = {}
        for incident in incidents:
            type_counts[incident.incident_type] = type_counts.get(incident.incident_type, 0) + 1
        
        return {
            "status": "success",
            "data": {
                "summary": {
                    "total_incidents": total_incidents,
                    "open_incidents": open_incidents,
                    "resolved_incidents": resolved_incidents,
                    "average_mttr_minutes": round(avg_mttr, 2),
                    "period_days": days
                },
                "incidents_by_severity": severity_counts,
                "incidents_by_type": type_counts,
                "incidents": [
                    {
                        "id": inc.id,
                        "endpoint_id": inc.endpoint_id,
                        "incident_type": inc.incident_type,
                        "severity": inc.severity,
                        "status": inc.status,
                        "start_time": inc.start_time.isoformat(),
                        "end_time": inc.end_time.isoformat() if inc.end_time else None,
                        "duration_seconds": inc.duration_seconds,
                        "resolution_time_minutes": inc.resolution_time_minutes,
                        "impact_description": inc.impact_description
                    } for inc in incidents
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar resumo de incidentes: {str(e)}")
    finally:
        session.close()


@sla_router.get("/performance-metrics")
async def get_performance_metrics(
    endpoint_id: Optional[int] = Query(None, description="ID do endpoint específico"),
    days: int = Query(7, description="Número de dias para análise"),
    session: Session = Depends(init_session),
    current_user = Depends(verify_token)
):
    """
    Retorna métricas de performance detalhadas.
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Construir query base
        query = session.query(PerformanceMetrics).filter(
            PerformanceMetrics.timestamp >= cutoff_date
        )
        
        if endpoint_id:
            query = query.filter(PerformanceMetrics.endpoint_id == endpoint_id)
            
        performance_metrics = query.order_by(PerformanceMetrics.timestamp.desc()).all()
        
        return {
            "status": "success",
            "data": {
                "metrics": [
                    {
                        "id": pm.id,
                        "endpoint_id": pm.endpoint_id,
                        "timestamp": pm.timestamp.isoformat(),
                        "response_time_percentiles": {
                            "p50": pm.response_time_p50,
                            "p90": pm.response_time_p90,
                            "p95": pm.response_time_p95,
                            "p99": pm.response_time_p99,
                            "p99_9": pm.response_time_p99_9
                        },
                        "response_time_stats": {
                            "avg": pm.response_time_avg,
                            "max": pm.response_time_max,
                            "min": pm.response_time_min
                        },
                        "error_metrics": {
                            "error_rate_percentage": pm.error_rate_percentage,
                            "total_requests": pm.total_requests,
                            "failed_requests": pm.failed_requests
                        },
                        "network_metrics": {
                            "jitter_ms": pm.jitter_ms,
                            "packet_loss_rate": pm.packet_loss_rate
                        },
                        "measurement_info": {
                            "period_minutes": pm.measurement_period_minutes,
                            "sample_count": pm.sample_count
                        }
                    } for pm in performance_metrics
                ],
                "summary": {
                    "total_measurements": len(performance_metrics),
                    "period_days": days,
                    "endpoint_filter": endpoint_id
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar métricas de performance: {str(e)}")
    finally:
        session.close()
